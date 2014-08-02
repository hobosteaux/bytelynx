
import json


DEFAULT_CONF = {
    'general': {
        'config_dir': 'data'
    },
    'net': {
        'port': 5969,
        'randomize_port': True,
        'ui_port': 2983,
        'max_ui_conns': 5
    },
    'kademlia': {
        'group': 7,
        'bucket_size': 20,
        'paralellism': 3,
        'keysize': 320,
        'keyfile': 'data/key.pem'
    }
}


class Config():
    """
    General class to hold the config.
    """
    # TODO: Make this handle multithreading / singleton

    def __init__(self, path):
        self._path = path
        self._load()

    def make_tree(self, category):
        """
        Takes a tree of keys separated by periods and creates them.
        """
        curr_loc = self._config
        for level in category.split('.'):
            curr_loc[level] = curr_loc.get(level, {})
            curr_loc = curr_loc[level]

    def __getitem__(self, key):
        return self._config[key]

    def __setitem__(self, key, value):
        self._config[key] = value
        self._save()

    def __delitem__(self, key):
        del(self._config[key])
        self._save()

    def _load(self):
        try:
            with open(self._path, 'r') as f:
                self._config = json.loads(f.read())
        except IOError:
            self._config = DEFAULT_CONF

    def _save(self):
        with open(self._path, 'w') as f:
            f.write(json.dumps(self._config, indent=4))
