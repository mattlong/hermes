import sys, logging, json, xmpp, select
from datetime import datetime

def debug(msg, indent=0):
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
        self.client.sendInitPresence()

    def send_message(self, body, to):
        debug('message on %s to %s: %s' % (self.name, to['JID'], body))
        message = xmpp.protocol.Message(to=to['JID'], body=body, typ='chat')
        self.client.send(message)

    def broadcast(self, body, exclude=()):
        debug('broadcast on %s: %s' % (self.name, body,))
        for member in filter(lambda m: m.get('RECEIVE', True) and m not in exclude, self.params['MEMBERS']):
            debug(member['JID'], indent=2)
            message = xmpp.protocol.Message(to=member['JID'], body=body, typ='chat')
            self.client.send(message)

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

        #process commands or treat as normal message
        if body == '/marco':
            self.send_message('polo', sender)
        else: #Normal broadcast
            broadcast_body = '[%s] %s' % (sender['NICK'], body,)
            self.broadcast(broadcast_body, exclude=(sender,))

def start_server(chatrooms={}):
    socket_list = {}
    for name, params in chatrooms.items():
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
