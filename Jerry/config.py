import os
from dataclasses import dataclass
from pathlib import Path
import json
import logging
import time

@dataclass
class AssistantConfig:
    """Configuration for the virtual assistant"""
    name: str = "Friday"
    voice_id: str = None
    language: str = "en-US"
    wake_word: str = "friday"
    weather_api_key: str = None
    news_api_key: str = None
    sample_rate: int = 16000
    recording_duration: int = 5
    screenshot_dir: Path = Path.home() / "Screenshots"
    
    @classmethod
    def load_config(cls):
        """Load configuration from environment variables"""
        return cls(
            weather_api_key=os.getenv("WEATHER_API_KEY"),
            news_api_key=os.getenv("NEWS_API_KEY")
        )
def save_to_file(self, filepath=None):
    """Save configuration to JSON file"""
    if filepath is None:
        filepath = Path.home() / ".assistant_config.json"
    
    try:
        with open(filepath, 'w') as f:
            # Convert Path objects to strings
            config_dict = {k: str(v) if isinstance(v, Path) else v 
                          for k, v in self.__dict__.items()}
            json.dump(config_dict, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        return False

@classmethod
def load_from_file(cls, filepath=None):
    """Load configuration from JSON file with environment variable fallback"""
    if filepath is None:
        filepath = Path.home() / ".assistant_config.json"
    
    config = cls()
    
    # Try to load from file
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    if key == "screenshot_dir":
                        setattr(config, key, Path(value))
                    else:
                        setattr(config, key, value)
            return config
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
    
    # Fall back to environment variables
    return cls.load_config()