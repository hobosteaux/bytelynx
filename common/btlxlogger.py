from os import path, makedirs
import logging


def get(module='main', mode=logging.DEBUG):
    from .config import get as get_config
    d = get_config()['general']['config_dir']
    ld = path.join(d, 'log')
    makedirs(ld, exist_ok=True)
    ln = path.join(ld, module.split('.')[0] + '.log')

    logger = logging.getLogger(module)
    if not logger.hasHandlers():
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        handler = logging.FileHandler(ln)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(mode)
    return logger
