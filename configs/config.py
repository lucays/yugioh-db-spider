import os
import yaml

config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config", "config.yml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

MYSQL_URI = config.get("MYSQL_URI")
PROXIES = config.get("PROXIES", "")
