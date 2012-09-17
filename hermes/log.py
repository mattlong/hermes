import logging
import logging.config

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
    logging.config.dictConfig(config_dict)
