"""
Configuration management for NOIR UI.
Handles application settings, theme configuration, and constants.
"""
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path
import json

@dataclass
class UIConfig:
    """UI-specific configuration settings."""
    grid_size: int = 10
    zoom_factor_in: float = 1.2
    zoom_factor_out: float = 0.8
    theme: Dict[str, str] = None

    def __post_init__(self):
        if self.theme is None:
            self.theme = {
                'primary': '#2C3E50',
                'secondary': '#34495E',
                'accent': '#3498DB',
                'background': '#ECF0F1'
            }

class Config:
    """Central configuration management class."""
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path('config.json')
        self.ui = UIConfig()
        self._load_config()

    def _load_config(self):
        """Load configuration from file if it exists."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                self.ui = UIConfig(**data.get('ui', {}))

    def save_config(self):
        """Save current configuration to file."""
        config_data = {
            'ui': {
                'grid_size': self.ui.grid_size,
                'zoom_factor_in': self.ui.zoom_factor_in,
                'zoom_factor_out': self.ui.zoom_factor_out,
                'theme': self.ui.theme
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
