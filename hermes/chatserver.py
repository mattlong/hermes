import sys, logging, json, xmpp, select, socket, re
from datetime import datetime

import hermes

def debug(msg, indent=0, quiet=False):
    if not quiet:
        print '%s%s%s' % (datetime.utcnow(), (indent+1)*' ', msg)

class HermesBot(object):
    command_patterns = []

    def __init__(self, name, params):
        self.command_patterns = []
        for pattern in type(self).command_patterns:
            self.command_patterns.append((re.compile(pattern[0]), pattern[1]))

        self.name = name
        self.params = params

        self.jid = xmpp.protocol.JID(self.params['JID'])
        self.client = xmpp.Client(self.jid.getDomain(), debug=[])

    def connect(self):
        conn = self.client.connect(server=self.params['SERVER'])
        if not conn:
            raise Exception("ERROR: could not connect to jabber")

        auth = self.client.auth(self.jid.getNode(), self.params['PASSWORD'])
        if not auth:
            raise Exception("ERROR: could not authenticate")

        self.client.RegisterDisconnectHandler(self.on_disconnect)
        self.client.RegisterHandler('message', self.on_message)
        self.client.sendInitPresence(requestRoster=1)

        #roster =  self.client.getRoster()
        #for jid in roster.keys():
        #    print jid
        #    print roster.getSubscription(jid)

    def invite_user(self, jid, inviter=None):
        if len(filter(lambda m: m['JID'] == jid, self.params['MEMBERS'])) > 0:
            if inviter:
                self.send_message('%s is already a member' % (jid,), inviter)
        else:
            self.broadcast('inviting %s to the room' % (jid,))
            self.client.sendPresence(jid=jid, typ='subscribed')

            subscribe_presence = xmpp.dispatcher.Presence(to=jid, typ='subscribe')
            if 'NICK' in self.params:
                #http://xmpp.org/extensions/xep-0172.html
                subscribe_presence.addChild(name='nick', namespace=xmpp.protocol.NS_NICK, payload=self.params['NICK'])
            self.client.send(subscribe_presence)

            new_member = { 'JID': jid, 'NICK': jid.split('@')[0] }
            self.params['MEMBERS'].append(new_member)
            self.send_message('You have been invited to chat in %s' % (self.name,), new_member)

    def kick_user(self, jid):
        for member in filter(lambda m: m['JID'] == jid, self.params['MEMBERS']):
            member['KICKED'] = True
            self.send_message('You have been kicked from %s' % (self.name,), member)

            self.client.sendPresence(jid=member['JID'], typ='unsubscribed')
            self.client.sendPresence(jid=member['JID'], typ='unsubscribe')
            self.broadcast('kicking %s from the room' % (jid,))

    def send_message(self, body, to, quiet=False, html_body=None):
        if to.get('MUTED'):
            to['QUEUED_MESSAGES'].append(body)
        else:
            debug('message on %s to %s: %s' % (self.name, to['JID'], body), quiet=quiet)

            message = xmpp.protocol.Message(to=to['JID'], body=body, typ='chat')

            if html_body:
                html = xmpp.Node('html', {'xmlns': 'http://jabber.org/protocol/xhtml-im'})
                html.addChild(node=xmpp.simplexml.XML2Node("<body xmlns='http://www.w3.org/1999/xhtml'>" + html_body.encode('utf-8') + "</body>"))
                message.addChild(node=html)

            self.client.send(message)

    def broadcast(self, body, html_body=None, exclude=()):
        debug('broadcast on %s: %s' % (self.name, body,))
        for member in filter(lambda m:
                not m.get('KICKED') and
                m.get('RECEIVE', True) and
                m not in exclude, self.params['MEMBERS']):
            debug(member['JID'], indent=2)
            self.send_message(body, member, html_body=html_body, quiet=True)

    def do_marco(self, sender, body, args):
        self.send_message('polo', sender)

    def do_invite(self, sender, body, args):
        for invitee in args:
            self.invite_user(invitee, inviter=sender)

    def do_kick(self, sender, body, args):
        if sender.get('ADMIN') != True: return
        for user in args:
            self.kick_user(user)

    def do_mute(self, sender, body, args):
        if sender.get('MUTED'):
            self.send_message('you are already muted', sender)
        else:
            self.broadcast('%s has muted this chatroom' % (sender['NICK'],))
            sender['QUEUED_MESSAGES'] = []
            sender['MUTED'] = True

    def do_unmute(self, sender, body, args):
        if sender.get('MUTED'):
            sender['MUTED'] = False
            self.broadcast('%s has unmuted this chatroom' % (sender['NICK'],))
            for msg in sender.get('QUEUED_MESSAGES', []):
                self.send_message(msg, sender)
            sender['QUEUED_MESSAGES'] = []
        else:
            self.send_message('you were not muted', sender)

    def on_disconnect(self):
        debug('ERROR: Disconnected from server!')
        #debug(str(self.client.reconnectAndReauth()))

    def on_message(self, con, event):
        msg_type = event.getType()
        nick = event.getFrom().getResource()
        from_jid = event.getFrom().getStripped()
        body = event.getBody()

        if msg_type == 'chat' and body is None:
            return

        debug('msg_type[%s] from[%s] nick[%s] body[%s]' % (msg_type, from_jid, nick, body,))

        sender = filter(lambda m: m['JID'] == from_jid, self.params['MEMBERS'])

        should_process = msg_type in ['message', 'chat', None] and body is not None and len(sender) == 1
        if not should_process: return
        sender = sender[0]

        for p in self.command_patterns:
            reg, cmd = p
            m = reg.match(body)
            if m:
                debug('pattern matched for bot command \'%s\'' % (cmd,))
                function = getattr(self, cmd, None) if cmd else None
                if function:
                    return function(sender, body, m)

        words = body.split(' ')
        cmd, args = words[0], words[1:]
        if cmd and cmd[0] == '/':
            cmd = cmd[1:]
        else:
            cmd, args = None, None

        function = getattr(self, 'do_'+cmd, None) if cmd else None
        try:
            if function:
                return function(sender, body, args)
            else: #normal broadcast
                broadcast_body = '[%s] %s' % (sender['NICK'], body,)
                return self.broadcast(broadcast_body, exclude=(sender,))
        except:
            exc_info = sys.exc_info()
            traceback.format_exception(exc_info[0], exc_info[1], exc_info[2])

def start_server(settings):
    print 'Hermes version %s' % (hermes.VERSION_STRING,)

    bots = []
    for name, params in settings.CHATROOMS.items():

        bot_class_str = params.get('CLASS', 'hermes.HermesBot')
        bot_class_path = bot_class_str.split('.')
        module, classname = '.'.join(bot_class_path[:-1]), bot_class_path[-1]
        #bot_class = __import__(bot_class_str)
        _ = __import__(module, globals(), locals(), [classname])
        bot_class = getattr(_, classname)
        bot = bot_class(name, params)
        bots.append(bot)

    while True:
        sockets = _get_sockets(bots)

        if len(sockets.keys()) == 0:
            debug('No chatrooms defined. Exiting.')
            return

        try:
            _listen(sockets)
        except socket.error, ex:
            if ex.errno == 9:
                print "Broken socket detected, regathering socket info..."

def _get_sockets(bots):
    sockets = {}
    #sockets[sys.stdin] = 'stdio'
    for bot in bots:
        bot.connect()
        sockets[bot.client.Connection._sock] = bot
    return sockets

def _listen(sockets):
    while True:
        (i , o, e) = select.select(sockets.keys(),[],[],1)
        for socket in i:
            if isinstance(sockets[socket], HermesBot):
                sockets[socket].client.Process(1)
            elif sockets[socket] == 'stdio':
                msg = sys.stdin.readline().rstrip('\r\n')
                debug('stdin: %s' % (msg,))
            else:
                raise Exception("Unknown socket type: %s" % repr(sockets[socket]))
