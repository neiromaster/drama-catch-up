import yaml


def load_config(path="config.yaml"):
    """Loads the configuration from a YAML file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None


def save_config(data, path="config.yaml"):
    """Saves the data to a YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
