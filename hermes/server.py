import sys, logging, xmpp, select, socket, time
from datetime import datetime

from .log import configure_logging
from .chatroom import Chatroom

logger = logging.getLogger(__name__)

#def debug(msg, indent=0, quiet=False):
#    if not quiet:
#        print '%s%s%s' % (datetime.utcnow(), (indent+1)*' ', msg)

def start_server(chatrooms={}, use_default_logging=True):
    if use_default_logging:
        configure_logging()

    logger.info('Starting Hermes chatroom server...')

    bots = []
    for name, params in chatrooms.items():

        bot_class_str = params.get('CLASS', 'hermes.Chatroom')
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
            if isinstance(sockets[socket], Chatroom):
                data_len = sockets[socket].client.Process(1)
                if data_len is None or data_len == 0:
                    raise Exception('Disconnected from server')
            #elif sockets[socket] == 'stdio':
            #    msg = sys.stdin.readline().rstrip('\r\n')
            #    logger.info('stdin: [%s]' % (msg,))
            else:
                raise Exception("Unknown socket type: %s" % repr(sockets[socket]))
