import argparse
import json
import sys

from scraper import print_banner, load_config, ScraperConfig, HCaptchaChallengeScraper
from scraper.logger import get_logger


def main() -> None:
    parser = argparse.ArgumentParser(description="hCaptcha challenge scraper")
    parser.add_argument("--config", default="config/config.json", help="Path to config JSON")
    args = parser.parse_args()
    try:
        print_banner()
        config_dict = load_config(args.config)
        config = ScraperConfig(**config_dict)
        print()

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print_banner()
        print()
        get_logger("Config").exception("Failed to load config from %s", args.config)
        raise SystemExit(1) from exc
    scraper = HCaptchaChallengeScraper(config)
    scraper.scrape()


if __name__ == "__main__":
    main()