"""
hermes Chatroom server
~~~~~~~~~~~~~~~~~~~~~~

Hermes is an extensible XMPP-based chatroom server written in Python.

Project homepage: https://github.com/mattlong/hermes

:copyright: (c) 2012 by Matt Long.
:license: ISC, see LICENSE for more details.
"""

from .server import run_server
from .chatroom import Chatroom
from .version import VERSION_STRING

__author__ = "Matt Long"
__copyright__ = "Copyright 2012, Matt Long"
__license__ = "ISC"
__version__ = VERSION_STRING
__maintainer__ = "Matt Long"
__status__ = "Development"

