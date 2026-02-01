#!/usr/bin/env python3
"""Chrome scraper service that connects to Chrome via DevTools protocol."""

import asyncio
import os
import signal
import socket
import subprocess
from pathlib import Path

import trafilatura
from aiohttp import web
from playwright.async_api import async_playwright

from scrape_to_md.config import get_config
from scrape_to_md.logging_config import setup_logging


# Logger will be initialized in main()
logger = None


def is_chrome_running(port: int = 9222) -> bool:
    """Check if Chrome's remote debugging port is accessible.

    Args:
        port: CDP port number

    Returns:
        True if Chrome is running on specified port
    """
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def launch_chrome(port: int, profile_dir: Path, chrome_path: str) -> subprocess.Popen:
    """Launch Chrome with remote debugging enabled.

    Args:
        port: CDP port number
        profile_dir: User data directory for Chrome profile
        chrome_path: Path to Chrome executable

    Returns:
        Chrome process
    """
    profile_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    logger.info(f"Launching Chrome with profile: {profile_dir}")
    # Start Chrome as a detached process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return process


class ChromeService:
    """Chrome scraper service using Playwright."""

    def __init__(self):
        """Initialize scraper service."""
        self.config = get_config()
        self.cdp_url = f"http://localhost:{self.config.cdp_port}"
        self.playwright = None
        self.browser = None
        self.chrome_process = None
        self.chrome_pid_file = self.config.pids_dir / "chrome_browser.pid"

    async def start(self):
        """Connect to existing Chrome instance, launching one if needed."""
        await self._ensure_chrome_running()

        self.playwright = await async_playwright().start()

        # Try to connect to Chrome via CDP with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
                logger.info(f"Connected to browser at {self.cdp_url}")
                break
            except Exception as e:
                logger.warning(f"Failed to connect to Chrome (attempt {attempt + 1}/{max_retries}): {e}")

                if "ECONNREFUSED" in str(e) or "connect" in str(e).lower():
                    # Chrome crashed or was killed, restart it
                    logger.info("Chrome connection refused, restarting Chrome...")
                    await self.cleanup_chrome()
                    await self._ensure_chrome_running()

                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
                    else:
                        raise RuntimeError(f"Failed to connect to Chrome after {max_retries} attempts: {e}")
                else:
                    # Different error, don't retry
                    raise

    async def _ensure_chrome_running(self):
        """Ensure Chrome process is running and ready."""
        if not is_chrome_running(self.config.cdp_port):
            logger.info("Chrome not running, launching...")

            # Find Chrome executable
            chrome_path = self.config.find_chrome_executable()

            self.chrome_process = launch_chrome(
                self.config.cdp_port,
                self.config.chrome_profile,
                chrome_path
            )

            # Save Chrome browser PID
            self.chrome_pid_file.parent.mkdir(parents=True, exist_ok=True)
            self.chrome_pid_file.write_text(str(self.chrome_process.pid))
            logger.info(f"Chrome browser PID: {self.chrome_process.pid}")

            # Wait for Chrome to be ready
            for _ in range(30):  # 30 second timeout
                await asyncio.sleep(1)
                if is_chrome_running(self.config.cdp_port):
                    logger.info("Chrome is ready")
                    break
            else:
                raise RuntimeError("Chrome failed to start within 30 seconds")

    async def stop(self):
        """Stop scraper and cleanup."""
        if self.browser:
            try:
                await self.browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")

        # Kill Chrome browser if we started it
        await self.cleanup_chrome()

    async def cleanup_chrome(self):
        """Kill Chrome browser process on shutdown."""
        if self.chrome_pid_file.exists():
            try:
                pid = int(self.chrome_pid_file.read_text())
                import os
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Stopped Chrome browser (PID {pid})")
                self.chrome_pid_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup Chrome: {e}")

    async def ensure_connected(self):
        """Ensure we have a valid browser connection with at least one context."""
        needs_reconnect = False

        try:
            # Check if browser is still connected
            if not self.browser or not self.browser.is_connected():
                needs_reconnect = True
            # Check if there are any contexts (windows)
            elif not self.browser.contexts:
                needs_reconnect = True
        except Exception as e:
            # Browser connection is broken
            logger.warning(f"Error checking browser connection: {e}")
            needs_reconnect = True

        if needs_reconnect:
            logger.info("Browser disconnected or no contexts, reconnecting...")
            await self.stop()
            await self.start()

            # If still no contexts after reconnect, we need to wait for a window
            if not self.browser.contexts:
                raise RuntimeError(
                    "No browser windows available. Open a Chrome window and try again."
                )

    async def scrape(self, url: str, selector: str = None) -> dict:
        """Scrape a URL.

        Args:
            url: URL to scrape
            selector: Optional CSS selector

        Returns:
            Dict with url, title, markdown, and error
        """
        await self.ensure_connected()

        # Get the default context (logged-in session)
        context = self.browser.contexts[0]
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            title = await page.title()

            if selector:
                element = await page.query_selector(selector)
                if element:
                    inner = await element.inner_html()
                    # Wrap in a document so trafilatura can process it
                    html = f"<html><body><article>{inner}</article></body></html>"
                else:
                    html = await page.content()
            else:
                html = await page.content()

            markdown = (
                trafilatura.extract(
                    html,
                    include_links=True,
                    include_images=True,
                    output_format="markdown",
                )
                or ""
            )

            return {"url": url, "title": title, "markdown": markdown, "error": None}

        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return {"url": url, "title": "", "markdown": "", "error": str(e)}
        finally:
            await page.close()


# Global scraper instance
scraper = None


async def handle_scrape(request: web.Request) -> web.Response:
    """Handle scrape requests."""
    data = await request.json()
    result = await scraper.scrape(data["url"], data.get("selector"))
    return web.json_response(result)


async def handle_health(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.Response(text="OK", status=200)


async def on_startup(app: web.Application):
    """Startup handler."""
    global scraper
    scraper = ChromeService()
    await scraper.start()
    logger.info("Chrome scraper service started")


async def on_cleanup(app: web.Application):
    """Cleanup handler."""
    if scraper:
        await scraper.stop()
    logger.info("Chrome scraper service stopped")


def create_app() -> web.Application:
    """Create aiohttp application."""
    app = web.Application()
    app.router.add_post("/scrape", handle_scrape)
    app.router.add_get("/health", handle_health)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


def main():
    """Main entry point for rt-chrome-scraper command."""
    global logger

    config = get_config()

    # Initialize logger
    logger = setup_logging(__name__, config.logs_dir / "chrome_scraper.log")

    # Save daemon PID
    daemon_pid_file = config.pids_dir / "chrome_service.pid"
    daemon_pid_file.parent.mkdir(parents=True, exist_ok=True)
    daemon_pid_file.write_text(str(os.getpid()))
    logger.info(f"Daemon PID: {os.getpid()}")

    # Register signal handlers for graceful shutdown
    def cleanup_and_exit(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        daemon_pid_file.unlink(missing_ok=True)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, cleanup_and_exit)
    signal.signal(signal.SIGINT, cleanup_and_exit)

    # Remove stale socket file if it exists
    config.socket_path.unlink(missing_ok=True)

    try:
        logger.info(f"Starting scraper server on {config.socket_path}")
        web.run_app(create_app(), path=str(config.socket_path))
    finally:
        # Cleanup on exit
        daemon_pid_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
