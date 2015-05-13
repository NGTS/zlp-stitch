import logging.config
import json
import os


def setup_logging(name):
    log_path = os.path.join(os.path.dirname(__file__), 'logging.json')
    with open(log_path) as infile:
        log_config = json.load(infile)

    new_config = {}
    for key in log_config:
        if key == 'handlers':
            new_handlers = {}
            for handler in log_config[key]:
                if 'filename' in log_config[key][handler].keys():
                    new = log_config[key][handler].copy()
                    new['filename'] = os.path.expanduser(new['filename'])
                    new_handlers[handler] = new
                else:
                    new_handlers[handler] = log_config[key][handler]
            new_config['handlers'] = new_handlers
        else:
            new_config[key] = log_config[key]

    logging.config.dictConfig(new_config)
    return logging.getLogger(name)
