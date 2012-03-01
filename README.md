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

## Commands

Hermes will interpret certain messages as commands and treats them differently from normal messagesd:

* `/marco` - Not sure if other people are getting your messages? Hermes replies to you (and only you) with "polo".

* `/mute` - **_Coming soon._** Queues up incoming messages so you're distraction free (at lease from your chatrooms). Others are informed that you're busy.

* `/unmute` - **_Coming soon._** Receive all queued messages. Others are informed that you're not busy anymore.

* `/invite <handle>` - **_Coming soon._** Invite new members to the chatroom.

## Upcoming Features

* **Persistence**: Allow chatroom details to be easily persisted in ways besides hardcoded python objects. Provide hooks to update settings on the fly.
* **Mute/unmute**: Don't want to be distracted? Have your messages queued up and waiting for you when you want them.
* **Invitations**: Manage chatroom membership. Depends on persistence support

## Is it any good?

Yes.
