import logging.config
import yaml
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

with open(f'{str(CURRENT_DIR)}/client_log_config.yaml', 'r') as stream:
    config = yaml.safe_load(stream)

logging.config.dictConfig(config)
