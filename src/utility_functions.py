import json
from pathlib import Path

def get_root():
    current_file_path = Path(__file__).resolve()
    while current_file_path.parent != current_file_path:  # Prevents infinite loops at root
        if (current_file_path / "config.json").exists() or (current_file_path / ".git").exists():
            return current_file_path
        current_file_path = current_file_path.parent
    raise RuntimeError("Project root not found.")

def get_config_path():
    project_root = get_root()
    config_path = Path(project_root) / "config.json"
    return config_path

def load_config():
    config_path = get_config_path()
    with open(config_path, "r") as file:
        return json.load(file)