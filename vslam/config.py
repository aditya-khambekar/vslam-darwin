import os

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def load(path: str = CONFIG_FILE) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)
