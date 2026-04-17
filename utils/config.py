import yaml
from utils.path import ROOT

def get_config():
    path = f"{ROOT}/config.yml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)