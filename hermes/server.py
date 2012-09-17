"""
hermes.server
~~~~~~~~~~~~~

This module contains the chatroom server setup and management for Hermes.
"""

import sys
import select
import socket
import time
import logging

from datetime import datetime

from .log import configure_logging
from .chatroom import Chatroom

logger = logging.getLogger(__name__)

#def debug(msg, indent=0, quiet=False):
#    if not quiet:
#        print '%s%s%s' % (datetime.utcnow(), (indent+1)*' ', msg)

def run_server(chatrooms, use_default_logging=True):
    """Sets up and serves specified chatrooms. Main entrypoint to Hermes.

    :param chatrooms: Dictionary of chatrooms to serve.
    :param use_default_logging: (optional) Boolean. Set to True if Hermes should setup its default logging configuration.
    """
    if use_default_logging:
        configure_logging()

    logger.info('Starting Hermes chatroom server...')

    bots = []
    for name, params in chatrooms.items():

        bot_class = params.get('CLASS', 'hermes.Chatroom')
        if type(bot_class) == type:
            pass
        else:
            bot_class_path = bot_class.split('.')
            if len(bot_class_path) == 1:
                module, classname = '__main__', bot_class_path[-1]
            else:
                module, classname = '.'.join(bot_class_path[:-1]), bot_class_path[-1]
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
    """Connects and gathers sockets for all chatrooms"""
    sockets = {}
    #sockets[sys.stdin] = 'stdio'
    for bot in bots:
        bot.connect()
        sockets[bot.client.Connection._sock] = bot
    return sockets

def _listen(sockets):
    """Main server loop. Listens for incoming events and dispatches them to appropriate chatroom"""
    while True:
        (i , o, e) = select.select(sockets.keys(),[],[],1)
        for socket in i:
            if isinstance(sockets[socket], Chatroom):
                data_len = sockets[socket].client.Process(1)
                if data_len is None or data_len == 0:
                    raise Exception('Disconnected from server')
            #elif sockets[socket] == 'stdio':
            #    msg = sys.stdin.readline().rstrip('\r\n')
            #    logger.info('stdin: [%s]' % (msg,))
            else:
                raise Exception("Unknown socket type: %s" % repr(sockets[socket]))
