import sys, logging, json, xmpp, select
from datetime import datetime

#from hermes import database

def debug(msg, indent=0, quiet=False):
    if not quiet:
        print '%s%s%s' % (datetime.utcnow(), (indent+1)*' ', msg)

class HermesBot(object):
    def __init__(self, name, params):
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
            self.client.sendPresence(jid=jid, typ='subscribe')

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

    def send_message(self, body, to, quiet=False):
        if to.get('MUTED'):
            to['QUEUED_MESSAGES'].append(body)
        else:
            debug('message on %s to %s: %s' % (self.name, to['JID'], body), quiet=quiet)
            message = xmpp.protocol.Message(to=to['JID'], body=body, typ='chat')
            self.client.send(message)

    def broadcast(self, body, exclude=()):
        debug('broadcast on %s: %s' % (self.name, body,))
        for member in filter(lambda m:
                not m.get('KICKED') and
                m.get('RECEIVE', True) and
                m not in exclude, self.params['MEMBERS']):
            debug(member['JID'], indent=2)
            self.send_message(body, member, quiet=True)

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

    def on_message(self, con, event):
        msg_type = event.getType()
        nick = event.getFrom().getResource()
        from_jid = event.getFrom().getStripped()
        body = event.getBody()
        debug('msg_type[%s] from[%s] nick[%s] body[%s]' % (msg_type, from_jid, nick, body,))

        sender = filter(lambda m: m['JID'] == from_jid, self.params['MEMBERS'])

        should_process = msg_type in ['message', 'chat', None] and body is not None and len(sender) == 1
        if not should_process: return
        sender = sender[0]

        words = body.split(' ')
        cmd, args = words[0], words[1:]
        if cmd and cmd[0] == '/':
            cmd = cmd[1:]
        else:
            cmd, args = None, None

        function = getattr(self, 'do_'+cmd, None) if cmd else None
        try:
            if function:
                function(sender, body, args)
            else: #normal broadcast
                broadcast_body = '[%s] %s' % (sender['NICK'], body,)
                self.broadcast(broadcast_body, exclude=(sender,))
        except:
            exc_info = sys.exc_info()
            traceback.format_exception(exc_info[0], exc_info[1], exc_info[2])

def start_server(settings):
    socket_list = {}

    #db = database.get_instance(settings.DATABASE)
    #db.setup()

    for name, params in settings.CHATROOMS.items():
        #name, params = db.save_room(name, params)
        bot = HermesBot(name, params)
        bot.connect()
        socket_list[bot.client.Connection._sock] = bot

    if len(socket_list.keys()) == 0:
        debug('No chatrooms defined. Exiting.')
        return

    #socket_list[sys.stdin] = 'stdio'

    while True:
        (i , o, e) = select.select(socket_list.keys(),[],[],1)
        for socket in i:
            if isinstance(socket_list[socket], HermesBot):
                socket_list[socket].client.Process(1)
            elif socket_list[socket] == 'stdio':
                msg = sys.stdin.readline().rstrip('\r\n')
                debug('stdin: %s' % (msg,))
            else:
                raise Exception("Unknown socket type: %s" % repr(socket_list[socket]))
