"""Configuration management for scrape_to_md."""

import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Config:
    """Application configuration."""

    output_dir: Path
    logs_dir: Path
    pids_dir: Path
    chrome_profile: Path
    socket_path: Path
    cdp_port: int

    def find_chrome_executable(self) -> str:
        """Find Chrome executable based on platform.

        Returns:
            Path to Chrome executable

        Raises:
            RuntimeError: If Chrome executable cannot be found
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        elif system == "Linux":
            paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
            ]
        elif system == "Windows":
            paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files\\Chromium\\Application\\chrome.exe",
            ]
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

        for path in paths:
            if Path(path).exists():
                return path

        raise RuntimeError(
            f"Chrome executable not found. Searched paths: {', '.join(paths)}"
        )


_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get application configuration (singleton).

    Loads configuration from ~/.config/scrape_to_md/config.yml if it exists,
    otherwise uses sensible defaults.

    Returns:
        Config instance
    """
    global _config_instance

    if _config_instance is not None:
        return _config_instance

    # Default paths
    home = Path.home()
    config_file = home / ".config" / "scrape_to_md" / "config.yml"
    data_dir = home / ".local" / "share" / "scrape_to_md"

    # Default configuration
    config_data = {
        "output_dir": str(home / "Documents" / "scraped"),
        "logs_dir": str(data_dir / "logs"),
        "pids_dir": str(data_dir / "pids"),
        "chrome_profile": str(data_dir / "chrome_profile"),
        "socket_path": str(data_dir / "chrome_scraper.sock"),
        "cdp_port": 9222,
    }

    # Load from config file if it exists
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                user_config = yaml.safe_load(f) or {}

            # Update with user config (top-level keys)
            if "output_dir" in user_config:
                config_data["output_dir"] = user_config["output_dir"]

            # Handle daemon-specific config
            if "daemon" in user_config and isinstance(user_config["daemon"], dict):
                daemon_config = user_config["daemon"]
                for key in ["logs_dir", "pids_dir", "chrome_profile", "socket_path", "cdp_port"]:
                    if key in daemon_config:
                        config_data[key] = daemon_config[key]
        except Exception as e:
            print(f"Warning: Failed to load config from {config_file}: {e}", file=sys.stderr)

    # Convert string paths to Path objects and expand ~
    _config_instance = Config(
        output_dir=Path(config_data["output_dir"]).expanduser(),
        logs_dir=Path(config_data["logs_dir"]).expanduser(),
        pids_dir=Path(config_data["pids_dir"]).expanduser(),
        chrome_profile=Path(config_data["chrome_profile"]).expanduser(),
        socket_path=Path(config_data["socket_path"]).expanduser(),
        cdp_port=int(config_data["cdp_port"]),
    )

    return _config_instance
