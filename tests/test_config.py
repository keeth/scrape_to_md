"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest

from scrape_to_md.config import Config, get_config


class TestConfig:
    """Test Config class."""

    def test_find_chrome_executable(self):
        """Test Chrome executable detection."""
        config = Config(
            logs_dir=Path("/tmp/logs"),
            pids_dir=Path("/tmp/pids"),
            chrome_profile=Path("/tmp/profile"),
            socket_path=Path("/tmp/socket"),
            cdp_port=9222,
        )

        # Should find Chrome on macOS, Linux, or Windows
        # This will raise RuntimeError if Chrome isn't installed
        try:
            chrome_path = config.find_chrome_executable()
            assert isinstance(chrome_path, str)
            assert len(chrome_path) > 0
        except RuntimeError as e:
            # Chrome not installed is acceptable for CI
            assert "Chrome executable not found" in str(e)

    def test_config_defaults(self):
        """Test default configuration values."""
        # Reset singleton for testing
        import scrape_to_md.config
        scrape_to_md.config._config_instance = None

        config = get_config()

        # Check that defaults are set
        assert config.cdp_port == 9222
        assert config.logs_dir.name == "logs"
        assert config.pids_dir.name == "pids"
        assert config.chrome_profile.name == "chrome_profile"
        assert config.socket_path.name == "chrome_scraper.sock"

        # Reset singleton
        scrape_to_md.config._config_instance = None

    def test_config_from_yaml(self):
        """Test loading configuration from YAML file."""
        # Reset singleton
        import scrape_to_md.config
        scrape_to_md.config._config_instance = None

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            config_path = Path(f.name)
            f.write("""
daemon:
  cdp_port: 9223
  chrome_profile: /custom/profile
  logs_dir: /custom/logs
""")

        try:
            # Monkey-patch the config file path
            original_home = Path.home
            temp_home = config_path.parent
            Path.home = lambda: temp_home

            # Create .config/scrape_to_md directory
            config_dir = temp_home / ".config" / "scrape_to_md"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.yml").write_text(config_path.read_text())

            # Get config
            config = get_config()

            # Verify custom values are loaded
            assert config.cdp_port == 9223
            assert str(config.chrome_profile) == "/custom/profile"
            assert str(config.logs_dir) == "/custom/logs"

        finally:
            # Cleanup
            Path.home = original_home
            config_path.unlink()
            scrape_to_md.config._config_instance = None
