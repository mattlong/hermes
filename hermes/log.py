"""
hermes.log
~~~~~~~~~~

This module contains logging configuration and setup for Hermes.
"""

from logging.config import dictConfig

DEFAULT_LOGGING = {
    'version': 1,
    'handlers': {
        'stdout': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'hermes': {
            'level': 'DEBUG',
            'handlers': ['stdout']
        },
    },
}

def configure_logging(config_dict=DEFAULT_LOGGING):
    """Configures logging with the specified configuration dictionary.

    :param config_dict: (optional) Standard Python logging configuration dictionary
    """

    dictConfig(config_dict)
