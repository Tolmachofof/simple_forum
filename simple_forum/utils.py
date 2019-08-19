import os
import pathlib

import yaml

BASE_PATH = pathlib.Path(__file__).parent.parent
# Путь до конфига по умолчанию
DEFAULT_CONFIG_PATH = BASE_PATH / 'conf' / 'conf.yaml'


def read_config(config_path=DEFAULT_CONFIG_PATH):
    with open(config_path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    config['database'] = {
        'host': os.environ.get('DATABASE_HOST', config['database']['host']),
        'port': int(
            os.environ.get('DATABASE_PORT', config['database']['port'])
        ),
        'database': os.environ.get(
            'DATABASE_NAME', config['database']['database']
        ),
        'user': os.environ.get('DATABASE_USER', config['database']['user']),
        'password': os.environ.get(
            'DATABASE_PASSWORD', config['database']['password']
        )
    }
    return config
