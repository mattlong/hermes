# hermes

Hermes is an extensible XMPP-based chatroom server written in Python. Easily setup and manage chatrooms for friends or colleagues.

## How it Works

Supply your own XMPP-based accounts (Google accounts work great!) to serve as chatroom hosts, add a bit of configuration, and that's it. All chatroom members are invited to chat with the host account which will in turn broadcast the message to all other members of the room.

## Usage

The "Hello World" usage of Hermes looks like this. Put the following in `chatserver.py`, update the user and chatroom info, and run it:

    from hermes import run_server
    
    brain = { 'JID': 'brain@wb.com', 'NICK': 'brain', 'ADMIN': True }
    pinky = { 'JID': 'pinky.suavo@wb.com', 'NICK': 'pinky' }
    
    chatrooms = {
        'world-domination-planning': {
            'JID': 'world.domination.planning@wb.com',
            'PASSWORD': 'thesamethingwedoeverynight',
            'SERVER': ('talk.google.com', 5223,),
            'MEMBERS': [pinky, brain],
        },
    }
    
    run_server(chatrooms)

## Installation

Available from PyPI: <http://pypi.python.org/pypi/hermes/>. pip is the recommended installation method:

    pip install hermes

## Commands

Hermes interprets some messages as commands:

* `/mute` - Mutes the chatroom so you can be distraction free. All messages are queued up for you for whenever you unmute the chatroom.

* `/unmute` - Unmutes the chatroom. Receive all messages that had been queued up for you while the chatroom was muted.

* `/invite <handle>` - Invite new members to the chatroom. Available to admins only.

* `/kick <handle>` - Kick members from the chatroom. Available to admins only.

* `/marco` - Not sure if you're still connected to the chatroom? Chatroom replies to you (and only you) with "polo".

## Extensibility

You can extend the base chatroom class `hermes.Chatroom` to modify or add extra functionality. Then specify your creation as the `CLASS` of your chatrooms:

	from hermes import run_server, Chatroom

	class BillyMaysChatroom(Chatroom):
    	command_patterns = ((r'.*', 'shout'),)

    	def shout(self, sender, body, match):
        	body = body.upper() #SHOUT IT
        	self.broadcast(body)

	chatrooms = {
        'world-domination-planning': {
        	'CLASS': 'BillyMaysChatroom',
            'JID': 'world.domination.planning@wb.com',
            'PASSWORD': 'thesamethingwedoeverynight',
            'SERVER': ('talk.google.com', 5223,),
            'MEMBERS': [pinky, brain],
        },
    }
	
	run_server(chatrooms)

## Upcoming Features

* **Persistence**: Allow chatroom configuration/state/history to be persisted

## Is it any good?

Yes.

Elaborate, you say? Hermes has been successfully used "in production" to run several chatrooms for the Crocodoc team since the first commit. It's good to have guinea pigs.

## License

Hermes is an ISC licensed library. See LICENSE for more details. If you insist on compensating me, I'd let you buy me a beer. Or just donate money to a good cause...that'd probably be best.

## Can I Contribute?

Yes, please do. Pull requests are great. I'll totally add a CONTRIBUTORS.txt when Hermes gets its first contributor.
