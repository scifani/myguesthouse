import os
import yaml


def load_config() -> dict:
    config_path = os.environ.get(
        'CONFIG_FILE',
        os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def resolve_text(value, lang: str, default_lang: str = 'it') -> str:
    """Return the right language variant of a config value.

    Accepts either a plain string (returned as-is) or a dict of the form
    {it: '...', en: '...'} — falls back to default_lang, then first available.
    """
    if isinstance(value, dict):
        return value.get(lang) or value.get(default_lang) or next(iter(value.values()), '')
    return value or ''
