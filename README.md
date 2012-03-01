# hermes

A simple python-based group chat server built on XMPP. Hermes lets you easily manage chatrooms for friends or colleagues.

## How it Works

Supply your own XMPP-based (e.g. GMail/Google Talk) accounts to serve as chatroom hosts, add a lil' bit of configuration, and start it. Chatroom members simply chat with the host account. Hermes broadcasts the message to all other members on its behalf.

## Usage

    from hermes import start_server
    
    pinky = { 'JID': 'p.suavo@wb.com', 'NICK': 'pinky' }
    
    brain = { 'JID': 'brain@wb.com', 'NICK': 'brain' }
    
    chatrooms = {
        'world-domination-planning': {
            'SERVER': ('talk.google.com', 5223,),
            'JID': 'wdp@foo.com',
            'PASSWORD': 'thesamethingwedoeverynight',
            'MEMBERS': [pinky, brain],
        },
    }
    
    start_server(chatrooms=chatrooms)

## Installation

Package available from PyPI: <http://pypi.python.org/pypi/hermes-chat/>. Install with:

    pip install hermes-chat

## Upcoming Features

* Persistence: allow chatroom details to be persisted besides hardcoded settings module. Hooks to update settings on the fly.
* Mute/unmute: queue up messages and send them all once unmuted.
* Invitations: manage chatroom membership. Depends on persistence support

## Is it any good?

Yes.
