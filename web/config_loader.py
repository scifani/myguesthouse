import os
import yaml


def load_config() -> dict:
    config_path = os.environ.get(
        'CONFIG_FILE',
        os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}
