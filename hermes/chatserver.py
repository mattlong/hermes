import sys, logging, json, xmpp, select, socket, re, time, traceback
from datetime import datetime

import hermes
from hermes.log import configure_logging

logger = logging.getLogger(__name__)

#def debug(msg, indent=0, quiet=False):
#    if not quiet:
#        print '%s%s%s' % (datetime.utcnow(), (indent+1)*' ', msg)

class HermesChatroom(object):

    #static property that can hold a list of regular expression/method name pairs. Each incoming message
    #is tested against each regex. On a match, the associated method is invoked to handle the message
    #instead of the standard message-handling pipeline.
    command_patterns = ()

    def __init__(self, name, params):
        self.command_patterns = []
        for pattern in type(self).command_patterns:
            self.command_patterns.append((re.compile(pattern[0]), pattern[1]))

        self.name = name
        self.params = params
        self.jid = xmpp.protocol.JID(self.params['JID'])

    def connect(self):
        self.client = xmpp.Client(self.jid.getDomain(), debug=[])
        conn = self.client.connect(server=self.params['SERVER'])
        if not conn:
            raise Exception("could not connect to server")

        auth = self.client.auth(self.jid.getNode(), self.params['PASSWORD'])
        if not auth:
            raise Exception("could not authenticate as chat server")

        #self.client.RegisterDisconnectHandler(self.on_disconnect)
        self.client.RegisterHandler('message', self.on_message)
        self.client.RegisterHandler('presence',self.on_presence)
        self.client.sendInitPresence(requestRoster=0)

        roster =  self.client.getRoster()
        for m in self.params['MEMBERS']:
            self.invite_user(m, roster=roster)

    def get_member(self, jid, default=None):
        member = filter(lambda m: m['JID'] == jid, self.params['MEMBERS'])
        if len(member) == 1:
            return member[0]
        elif len(member) == 0:
            return default
        else:
            raise Exception('Multple members have the same JID of [%s]' % (jid,))

    def is_member(self, m):
        if isinstance(m, basestring):
            jid = m
        else:
            jid = m['JID']

        return len(filter(lambda m: m['JID'] == jid and m['STATUS'] in ('ACTIVE', 'INVITED'), self.params['MEMBERS'])) > 0

    def invite_user(self, new_member, inviter=None, roster=None):
        roster = roster or self.client.getRoster()
        jid = new_member['JID']

        if jid in roster.keys() and roster.getSubscription(jid) == 'both':
            new_member['STATUS'] = 'ACTIVE'
            if inviter:
                self.send_message('%s is already a member' % (jid,), inviter)
        else:
            new_member['STATUS'] = 'INVITED'
            self.broadcast('inviting %s to the room' % (jid,))

            #Add nickname according to http://xmpp.org/extensions/xep-0172.html
            subscribe_presence = xmpp.dispatcher.Presence(to=jid, typ='subscribe')
            if 'NICK' in self.params:
                subscribe_presence.addChild(name='nick', namespace=xmpp.protocol.NS_NICK, payload=self.params['NICK'])
            self.client.send(subscribe_presence)

        if not self.is_member(new_member):
            new_member.setdefault('NICK', jid.split('@')[0])
            self.params['MEMBERS'].append(new_member)

    def kick_user(self, jid):
        for member in filter(lambda m: m['JID'] == jid, self.params['MEMBERS']):
            member['STATUS'] = 'KICKED'
            self.send_message('You have been kicked from %s' % (self.name,), member)

            self.client.sendPresence(jid=member['JID'], typ='unsubscribed')
            self.client.sendPresence(jid=member['JID'], typ='unsubscribe')
            self.broadcast('kicking %s from the room' % (jid,))

    def send_message(self, body, to, quiet=False, html_body=None):
        if to.get('MUTED'):
            to['QUEUED_MESSAGES'].append(body)
        else:
            if not quiet:
                logger.info('message on %s to %s: %s' % (self.name, to['JID'], body))

            message = xmpp.protocol.Message(to=to['JID'], body=body, typ='chat')
            if html_body:
                html = xmpp.Node('html', {'xmlns': 'http://jabber.org/protocol/xhtml-im'})
                html.addChild(node=xmpp.simplexml.XML2Node("<body xmlns='http://www.w3.org/1999/xhtml'>" + html_body.encode('utf-8') + "</body>"))
                message.addChild(node=html)

            self.client.send(message)

    def broadcast(self, body, html_body=None, exclude=()):
        logger.info('broadcast on %s: %s' % (self.name, body,))
        for member in filter(lambda m: m['STATUS'] == 'ACTIVE' and m not in exclude, self.params['MEMBERS']):
            logger.debug(member['JID'])
            self.send_message(body, member, html_body=html_body, quiet=True)

    ### Command handlers ###

    def do_marco(self, sender, body, args):
        self.send_message('polo', sender)

    def do_invite(self, sender, body, args):
        for invitee in args:
            new_member = { 'JID': invitee }
            self.invite_user(new_member, inviter=sender)

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

    ### XMPP event handlers ###

    def on_disconnect(self):
        logger.error('Disconnected from server!')

    def on_presence(self, session, presence):
        if presence.getType() == 'subscribe':
            from_jid = presence.getFrom()
            if self.is_member(from_jid.getStripped()):
                logger.info('Acknowledging subscription request from [%s]' % (from_jid,))
                self.client.sendPresence(jid=from_jid, typ='subscribed')
                member = self.get_member(from_jid)
                member['STATUS'] = 'ACTIVE'
                self.broadcast('%s has accepted their invitation!' % (from_jid,))
            else:
                #TODO: show that a user has requested membership?
                pass
        else:
            logger.info('Unhandled presence stanza of type [%s] from [%s]' % (presence.getType(), presence.getFrom()))

    def on_message(self, con, event):
        msg_type = event.getType()
        nick = event.getFrom().getResource()
        from_jid = event.getFrom().getStripped()
        body = event.getBody()

        if msg_type == 'chat' and body is None:
            return

        logger.debug('msg_type[%s] from[%s] nick[%s] body[%s]' % (msg_type, from_jid, nick, body,))

        sender = filter(lambda m: m['JID'] == from_jid, self.params['MEMBERS'])

        should_process = msg_type in ['message', 'chat', None] and body is not None and len(sender) == 1
        if not should_process: return
        sender = sender[0]

        for p in self.command_patterns:
            reg, cmd = p
            m = reg.match(body)
            if m:
                logger.info('pattern matched for bot command \'%s\'' % (cmd,))
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

def start_server(chatrooms={}, use_default_logging=True):
    if use_default_logging:
        configure_logging()

    logger.info('Hermes version %s' % (hermes.VERSION_STRING,))

    bots = []
    for name, params in chatrooms.items():

        bot_class_str = params.get('CLASS', 'hermes.HermesChatroom')
        bot_class_path = bot_class_str.split('.')
        module, classname = '.'.join(bot_class_path[:-1]), bot_class_path[-1]
        #bot_class = __import__(bot_class_str)
        _ = __import__(module, globals(), locals(), [classname])
        bot_class = getattr(_, classname)
        bot = bot_class(name, params)
        bots.append(bot)

    while True:
        try:
            logger.info("Connecting to servers...")
            sockets = _get_sockets(bots)
            if len(sockets.keys()) == 0:
                logger.info('No chatrooms defined. Exiting.')
                return

            _listen(sockets)
        except socket.error, ex:
            if ex.errno == 9:
                logger.exception('broken socket detected')
            else:
                logger.exception('Unknown socket error %d' % (ex.errno,))
        except Exception:
            logger.exception('Unexpected exception')
            time.sleep(1)

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
            if isinstance(sockets[socket], HermesChatroom):
                data_len = sockets[socket].client.Process(1)
                if data_len is None or data_len == 0:
                    raise Exception('Disconnected from server')
            #elif sockets[socket] == 'stdio':
            #    msg = sys.stdin.readline().rstrip('\r\n')
            #    logger.info('stdin: [%s]' % (msg,))
            else:
                raise Exception("Unknown socket type: %s" % repr(sockets[socket]))
