import json
import os
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')


def get_bring_data(file_name):
    if file_name == 'debug':
        fp = os.path.join(CONFIG_DIR, file_name)
        if not os.path.exists(fp):
            return False
    fp = os.path.join(CONFIG_DIR, file_name)
    with open(fp, 'r') as f:
        return json.load(f)
