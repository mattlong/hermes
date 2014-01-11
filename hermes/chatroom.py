"""
hermes.chatroom
~~~~~~~~~~~~~~~

This module contains the base chatroom functionality for Hermes.
"""

import re
import xmpp
import logging

logger = logging.getLogger(__name__)

class Chatroom(object):
    """Base chatroom class. Implements default broadcast logic and handles basic chatroom commands."""

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
        """Connect to the chatroom's server, sets up handlers, invites members as needed."""
        for m in self.params['MEMBERS']:
            m['ONLINE'] = 0
            m.setdefault('STATUS', 'INVITED')

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
        """Get a chatroom member by JID"""
        member = filter(lambda m: m['JID'] == jid, self.params['MEMBERS'])
        if len(member) == 1:
            return member[0]
        elif len(member) == 0:
            return default
        else:
            raise Exception('Multple members have the same JID of [%s]' % (jid,))

    def is_member(self, m):
        """Check if a user is a member of the chatroom"""
        if not m:
            return False
        elif isinstance(m, basestring):
            jid = m
        else:
            jid = m['JID']

        is_member = len(filter(lambda m: m['JID'] == jid and m.get('STATUS') in ('ACTIVE', 'INVITED'), self.params['MEMBERS'])) > 0

        return is_member

    def invite_user(self, new_member, inviter=None, roster=None):
        """Invites a new member to the chatroom"""
        roster = roster or self.client.getRoster()
        jid = new_member['JID']

        logger.info('roster %s %s' % (jid, roster.getSubscription(jid)))
        if jid in roster.keys() and roster.getSubscription(jid) in ['both', 'to']:
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
        """Kicks a member from the chatroom. Kicked user will receive no more messages."""
        for member in filter(lambda m: m['JID'] == jid, self.params['MEMBERS']):
            member['STATUS'] = 'KICKED'
            self.send_message('You have been kicked from %s' % (self.name,), member)

            self.client.sendPresence(jid=member['JID'], typ='unsubscribed')
            self.client.sendPresence(jid=member['JID'], typ='unsubscribe')
            self.broadcast('kicking %s from the room' % (jid,))

    def send_message(self, body, to, quiet=False, html_body=None):
        """Send a message to a single member"""
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
        """Broadcast a message to users in the chatroom"""
        logger.info('broadcast on %s: %s' % (self.name, body,))
        for member in filter(lambda m: m.get('STATUS') == 'ACTIVE' and m not in exclude, self.params['MEMBERS']):
            logger.debug(member['JID'])
            self.send_message(body, member, html_body=html_body, quiet=True)

    ### Command handlers ###

    def do_marco(self, sender, body, args):
        """Respond with 'polo' to the user"""
        self.send_message('polo', sender)

    def do_invite(self, sender, body, args):
        """Invite members to the chatroom on a user's behalf"""
        for invitee in args:
            new_member = { 'JID': invitee }
            self.invite_user(new_member, inviter=sender)

    def do_kick(self, sender, body, args):
        """Kick a member from the chatroom. Must be Admin to kick users"""
        if sender.get('ADMIN') != True: return
        for user in args:
            self.kick_user(user)

    def do_mute(self, sender, body, args):
        """Temporarily mutes chatroom for a user"""
        if sender.get('MUTED'):
            self.send_message('you are already muted', sender)
        else:
            self.broadcast('%s has muted this chatroom' % (sender['NICK'],))
            sender['QUEUED_MESSAGES'] = []
            sender['MUTED'] = True

    def do_unmute(self, sender, body, args):
        """Unmutes the chatroom for a user"""
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
        """Handler for disconnection events"""
        logger.error('Disconnected from server!')

    def on_presence(self, session, presence):
        """Handles presence stanzas"""
        from_jid = presence.getFrom()
        is_member = self.is_member(from_jid.getStripped())
        if is_member:
            member = self.get_member(from_jid.getStripped())
        else:
            member = None

        logger.info('presence: from=%s is_member=%s type=%s' % (from_jid, is_member, presence.getType()))

        if presence.getType() == 'subscribed':
            if is_member:
                logger.info('[%s] accepted their invitation' % (from_jid,))
                member['STATUS'] = 'ACTIVE'
            else:
                #TODO: user accepted, but is no longer be on the roster, unsubscribe?
                pass
        elif presence.getType() == 'subscribe':
            if is_member:
                logger.info('Acknowledging subscription request from [%s]' % (from_jid,))
                self.client.sendPresence(jid=from_jid, typ='subscribed')
                member['STATUS'] = 'ACTIVE'
                self.broadcast('%s has accepted their invitation!' % (from_jid,))
            else:
                #TODO: show that a user has requested membership?
                pass
        elif presence.getType() == None:
            if is_member:
                member['ONLINE'] += 1
        elif presence.getType() == 'unavailable':
            if is_member:
                member['ONLINE'] -= 1
        else:
            logger.info('Unhandled presence stanza of type [%s] from [%s]' % (presence.getType(), from_jid))

    def on_message(self, con, event):
        """Handles messge stanzas"""
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

        try:
            for p in self.command_patterns:
                reg, cmd = p
                m = reg.match(body)
                if m:
                    logger.info('pattern matched for bot command \'%s\'' % (cmd,))
                    function = getattr(self, str(cmd), None)
                    if function:
                        return function(sender, body, m)

            words = body.split(' ')
            cmd, args = words[0], words[1:]
            if cmd and cmd[0] == '/':
                cmd = cmd[1:]
                command_handler = getattr(self, 'do_'+cmd, None)
                if command_handler:
                    return command_handler(sender, body, args)

            broadcast_body = '[%s] %s' % (sender['NICK'], body,)
            return self.broadcast(broadcast_body, exclude=(sender,))
        except:
            logger.exception('Error handling message [%s] from [%s]' % (body, sender['JID']))
