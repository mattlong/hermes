# hermes

Hermes is an extensible XMPP-based chatroom server written in Python. Easily setup and manage chatrooms for friends or colleagues.

## How it Works

Supply your own XMPP-based accounts (Google accounts work great!) to serve as chatroom hosts, add a bit of configuration, and that's it. All chatroom members are invited to chat with the host account which will in turn broadcast the message to all other members of the room.

## Usage

The "Hello World" usage of Hermes looks like this. Put the following in `chatserver.py`, update the user info and chatroom connection info, and run it:

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

* `/mute` - Silences (and queues up) all chatroom activity until you unmute it so you can be distraction free.

* `/unmute` - Receive aqueued messages.

* `/invite <handle>` - Invite new members to the chatroom. admins only

* `/kick <handle>` - Invite new members to the chatroom. admins only.

* `/marco` - Not sure if you're still connected to the chatroom? Chatroom replies to you (and only you) with "polo"

## Extensibility

It's easy to extend the functionality chatroom. Extend the base chatroom class `hermes.HermesChatroom` to modify or add extra functionality. Then specify it as the `CLASS` class your chatrooms:

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
	
	run_server(chatrooms, use_default_logging=True)

## Upcoming Features

* **Persistence**: Allow chatroom configuration/state/history to be persisted

## Is it any good?

Yes.

Elaborate, you say? Hermes has been successfully used "in production" to run several chatrooms for the Crocodoc team since the first commit. It's good to have guinea pigs.

## License

Hermes is an ISC licensed library. See LICENSE for more details.

## Can I Contribute?

Yes, please do! Pull requests are great!
