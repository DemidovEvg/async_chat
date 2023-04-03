import logging.config
import yaml
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
log_folder = CURRENT_DIR.parent / 'log'
Path(log_folder).parents[0].mkdir(parents=True, exist_ok=True)

config = f'{str(CURRENT_DIR)}/client_log_config.yaml'
if Path(config).is_file():
    with open(config, 'r') as stream:
        config = yaml.safe_load(stream)

    logging.config.dictConfig(config)
