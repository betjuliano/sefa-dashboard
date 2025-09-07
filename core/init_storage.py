"""
Initialize local storage directory structure
"""
import os
import json
from .utils import ensure_directory_structure


def initialize_local_storage(base_path: str = "data") -> None:
    """
    Initialize the local storage directory structure and default files
    
    Args:
        base_path: Base path for data storage (default: "data")
    """
    # Create directory structure
    ensure_directory_structure(base_path)
    
    # Create users.json if it doesn't exist
    users_file = os.path.join(base_path, "users", "users.json")
    if not os.path.exists(users_file):
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump({"users": {}}, f, indent=2)
    
    # Create system config if it doesn't exist
    config_file = os.path.join(base_path, "shared", "system_config.json")
    if not os.path.exists(config_file):
        default_config = {
            "version": "1.0",
            "storage_format": "local",
            "backup_enabled": True,
            "max_file_size_mb": 100,
            "allowed_extensions": [".csv", ".xlsx", ".xls"],
            "created_at": "2024-01-01T00:00:00Z"
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
    
    print(f"Local storage initialized at: {os.path.abspath(base_path)}")


if __name__ == "__main__":
    initialize_local_storage()