from os import path, makedirs
import logging


def get(module='main', mode=logging.DEBUG):
    from .config import get as get_config
    d = get_config()['general']['config_dir']
    ld = path.join(d, 'log')
    makedirs(ld, exist_ok=True)
    root = module.split('.')[0]
    ln = path.join(ld, root + '.log')

    bl = logging.getLogger(root)
    if not bl.hasHandlers():
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        handler = logging.FileHandler(ln)
        handler.setFormatter(formatter)
        bl.addHandler(handler)
        bl.setLevel(mode)

    return logging.getLogger(module)
