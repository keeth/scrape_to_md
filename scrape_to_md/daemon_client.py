"""Client for communicating with the Chrome daemon service."""

import socket
from pathlib import Path

import aiohttp
import yaml


def is_daemon_running(socket_path: Path) -> bool:
    """Check if daemon is running by testing socket connection.

    Args:
        socket_path: Path to Unix socket

    Returns:
        True if daemon is running and accepting connections
    """
    if not socket_path.exists():
        return False

    try:
        # Try to connect to the socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect(str(socket_path))
        sock.close()
        return True
    except (socket.error, OSError):
        return False


async def scrape_via_daemon(url: str) -> str:
    """Scrape URL using daemon service.

    Args:
        url: URL to scrape

    Returns:
        Markdown content with frontmatter

    Raises:
        RuntimeError: If daemon request fails
    """
    from scrape_to_md.config import get_config

    config = get_config()

    # Connect to Unix socket using aiohttp UnixConnector
    connector = aiohttp.UnixConnector(path=str(config.socket_path))

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            # POST to /scrape endpoint
            async with session.post(
                "http://localhost/scrape",
                json={"url": url, "selector": None},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(
                        f"Daemon returned status {resp.status}: {await resp.text()}"
                    )
                result = await resp.json()
    except aiohttp.ClientError as e:
        raise RuntimeError(f"Failed to connect to daemon: {e}")

    # Check for errors in response
    if result.get("error"):
        raise RuntimeError(f"Daemon scraping failed: {result['error']}")

    # Create markdown with properly escaped YAML frontmatter (same format as web.py)
    title = result.get("title", "")
    markdown = result.get("markdown", "")

    # Create properly escaped YAML frontmatter
    frontmatter = {
        'url': url,
        'title': title,
        'source': 'web',
    }

    yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

    content = f"""---
{yaml_frontmatter}---

{markdown}
"""

    return content
