import logging.config
import yaml


with open('./log_config/client_log_config.yaml', 'r') as stream:
    config = yaml.safe_load(stream)

logging.config.dictConfig(config)
