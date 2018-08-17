import os
import json
CONFIG_FILE = '../config.json'

def load_config(var_type, script):
    """
    Load arguments and global variables.

    var_type : str
        Options are: args, globals

    script : str
        Script name e.g. twitter, rich_list
    """

    if not os.path.isfile(CONFIG_FILE):
        raise ValueError('No config.json file found.')

    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    if var_type == 'args':
        args = {k: v for k, v in config[script].items() if k != 'global'}
        return args

    elif var_type == 'globals':
        global_vars = {**config['global'], **config[script]['global']}
        global_vars = {k.upper(): v for k, v in global_vars.items()}
        return global_vars

    else:
        raise ValueError('Please specify var_type')
