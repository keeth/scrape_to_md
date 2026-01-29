#!/usr/bin/env python3
"""Simple CLI for scraping URLs to markdown."""
import argparse
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from scrape_to_md.config import get_config
from scrape_to_md.daemon_client import is_daemon_running, scrape_via_daemon
from scrape_to_md.detector import detect_url_type
from scrape_to_md.pdf import scrape_pdf
from scrape_to_md.web import scrape_web
from scrape_to_md.youtube import scrape_youtube


def get_output_dir() -> Path:
    """Get output directory from config or use default.

    Returns:
        Path to output directory
    """
    # Check for config file
    config_file = Path.home() / ".config" / "scrape_to_md" / "config.yml"
    if config_file.exists():
        import yaml
        try:
            config = yaml.safe_load(config_file.read_text())
            if 'output_dir' in config:
                return Path(config['output_dir']).expanduser()
        except Exception:
            pass

    # Default output directory
    return Path.home() / "Documents" / "scraped"


async def scrape_url(url: str, output_dir: Path | None = None) -> Path:
    """Scrape a URL and save to markdown.

    Args:
        url: URL to scrape
        output_dir: Optional output directory (uses default if not provided)

    Returns:
        Path to output file

    Raises:
        RuntimeError: If scraping fails
    """
    if output_dir is None:
        output_dir = get_output_dir()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Detect URL type
    url_type = detect_url_type(url)

    # Web scraping: use daemon (auto-start if needed)
    if url_type == "web":
        config = get_config()

        # Start daemon if not running
        if not is_daemon_running(config.socket_path):
            print("Starting daemon...", file=sys.stderr)
            if start_daemon_background():
                print("Daemon started", file=sys.stderr)
            else:
                print(
                    "Warning: Failed to start daemon, falling back to direct scraping",
                    file=sys.stderr,
                )

        # Try to use daemon if available
        if is_daemon_running(config.socket_path):
            try:
                return await scrape_via_daemon(url, output_dir)
            except RuntimeError as e:
                print(
                    f"Warning: Daemon failed ({e}), falling back to direct scraping",
                    file=sys.stderr,
                )

        # Fall back to direct scraping
        return await scrape_web(url, output_dir)

    # Direct scraping for YouTube and PDF
    if url_type == "youtube":
        return scrape_youtube(url, output_dir)
    elif url_type == "pdf":
        return scrape_pdf(url, output_dir)
    else:
        # Shouldn't reach here, but handle gracefully
        return await scrape_web(url, output_dir)


def start_daemon_background():
    """Start daemon in background.

    Returns:
        True if daemon was started, False if already running
    """
    config = get_config()

    # Check if already running
    if is_daemon_running(config.socket_path):
        return False

    # Start daemon in background
    subprocess.Popen(
        [sys.executable, "-m", "scrape_to_md.chrome_service"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Wait for daemon to be ready (up to 5 seconds)
    for _ in range(50):
        time.sleep(0.1)
        if is_daemon_running(config.socket_path):
            return True

    # Daemon didn't start in time
    return False


def handle_serve_start():
    """Start daemon in foreground."""
    from scrape_to_md.chrome_service import main as chrome_main

    chrome_main()


def handle_serve_stop():
    """Stop running daemon."""
    config = get_config()
    pid_file = config.pids_dir / "chrome_service.pid"

    if not pid_file.exists():
        print("Daemon is not running")
        return

    try:
        pid = int(pid_file.read_text())
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped daemon (PID {pid})")
    except ProcessLookupError:
        print("Daemon process not found, cleaning up stale PID file")
        pid_file.unlink()
    except Exception as e:
        print(f"Error stopping daemon: {e}", file=sys.stderr)
        sys.exit(1)


def handle_serve_status():
    """Check daemon status."""
    config = get_config()
    pid_file = config.pids_dir / "chrome_service.pid"

    if is_daemon_running(config.socket_path):
        if pid_file.exists():
            pid = int(pid_file.read_text())
            print(f"Daemon is running (PID {pid})")
        else:
            print("Daemon is running")
    else:
        print("Daemon is not running")
        if pid_file.exists():
            print("Warning: Stale PID file found")


def handle_init():
    """Create default configuration file."""
    config_file = Path.home() / ".config" / "scrape_to_md" / "config.yml"

    # Check if config already exists
    if config_file.exists():
        print(f"Config file already exists at {config_file}")
        response = input("Overwrite? (y/N): ")
        if response.lower() != "y":
            print("Init cancelled")
            return

    # Create config directory
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Default configuration
    default_config = """# scrape_to_md configuration

# Default output directory for scraped content
output_dir: ~/Documents/scraped

# Optional daemon configuration (defaults shown)
daemon:
  # Chrome DevTools Protocol port
  cdp_port: 9222

  # Chrome profile directory (maintains sessions/cookies)
  chrome_profile: ~/.local/share/scrape_to_md/chrome_profile

  # Log files directory
  logs_dir: ~/.local/share/scrape_to_md/logs

  # Unix socket path for daemon communication
  socket_path: ~/.local/share/scrape_to_md/chrome_scraper.sock
"""

    # Write config file
    config_file.write_text(default_config)
    print(f"Created config file at {config_file}")
    print("\nYou can now edit this file to customize your settings.")


def main():
    """Main CLI entry point."""
    # Check for subcommands
    if len(sys.argv) > 1:
        subcommand = sys.argv[1]

        # Handle 'init' subcommand
        if subcommand == "init":
            handle_init()
            return

        # Handle 'serve' subcommand
        if subcommand == "serve":
            parser = argparse.ArgumentParser(description="Manage daemon service")
            parser.add_argument("command", choices=["serve"], help="Subcommand")
            parser.add_argument("--stop", action="store_true", help="Stop daemon")
            parser.add_argument("--status", action="store_true", help="Check daemon status")

            args = parser.parse_args()

            if args.stop:
                handle_serve_stop()
            elif args.status:
                handle_serve_status()
            else:
                # Start daemon
                handle_serve_start()
            return

    # Default: scrape command (backward compatible)
    parser = argparse.ArgumentParser(
        description="Scrape URLs to markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  scrape_to_md https://example.com/article
  scrape_to_md https://youtube.com/watch?v=abc123
  scrape_to_md https://example.com/document.pdf
  scrape_to_md https://example.com/page -o ~/my-docs

Setup:
  scrape_to_md init               # Create default config file

Daemon commands:
  scrape_to_md serve              # Start daemon in foreground
  scrape_to_md serve --stop       # Stop daemon
  scrape_to_md serve --status     # Check daemon status

Note: Web scraping automatically launches daemon in background if not running.
      Use 'serve' command to run daemon in foreground for debugging.

Config file: ~/.config/scrape_to_md/config.yml
  Run 'scrape_to_md init' to create a default config file.
        """,
    )
    parser.add_argument("url", help="URL to scrape")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory (default: ~/Documents/scraped or from config)",
    )

    args = parser.parse_args()

    try:
        output_file = asyncio.run(scrape_url(args.url, args.output))
        print(output_file)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
