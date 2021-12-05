import os
import yaml

config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.yml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

MYSQL_URI = config['MYSQL_URI']
PROXIES = config['PROXIES']
