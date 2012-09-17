import sys
sys.path.append('..')

from hermes import run_server, Chatroom

from settings import chatrooms

class BillyMaysChatroom(Chatroom):
    command_patterns = ((r'.*', 'shout'),)

    def shout(self, sender, body, match):
        body = body.upper() #SHOUT IT
        self.broadcast(body)

run_server(chatrooms, use_default_logging=True)
