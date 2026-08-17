import json
from dataclasses import dataclass
from pathlib import Path

from .logger import get_logger

DEFAULT_CONFIG_PATH = "config/config.json"
CHALLENGES_DIR = Path("challenges")
DEFAULT_RETRY_DELAY = 3

@dataclass(slots=True)
class ScraperConfig:
    proxy: str
    sitekey: str
    url: str
    max_challenges: int = 30
    delay_sec: float = 0.0


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    config_log = get_logger("Config")
    config_log.info("Loading %s", config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    required = ("sitekey", "url")
    missing = [k for k in required if k not in config]
    if missing:
        raise KeyError(f"Missing configuration values: {', '.join(missing)}")
    config_log.ok("Loaded %s", config_path)
    return config