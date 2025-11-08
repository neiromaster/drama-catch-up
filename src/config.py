from typing import Any

import yaml


def load_config(path: str = "config.yaml") -> dict[str, Any] | None:
    """Loads the configuration from a YAML file."""
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None


def save_config(data: dict[str, Any], path: str = "config.yaml") -> None:
    """Saves the data to a YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
