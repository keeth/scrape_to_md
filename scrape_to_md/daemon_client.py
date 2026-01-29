"""Client for communicating with the Chrome daemon service."""

import socket
from pathlib import Path

import aiohttp


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


async def scrape_via_daemon(url: str, output_dir: Path) -> Path:
    """Scrape URL using daemon service.

    Args:
        url: URL to scrape
        output_dir: Directory to save output

    Returns:
        Path to output markdown file

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

    # Create markdown with frontmatter (same format as web.py)
    title = result.get("title", "")
    markdown = result.get("markdown", "")

    # Create frontmatter
    frontmatter = f"""---
url: {url}
title: {title}
source: web
---

{markdown}
"""

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename from title
    if title:
        # Take first 50 chars and sanitize
        filename = title[:50]
        # Replace filesystem-unfriendly characters (including spaces) with underscore
        filename = "".join(c if c.isalnum() else "_" for c in filename)
        # Remove leading/trailing underscores and collapse multiple underscores
        filename = "_".join(filter(None, filename.split("_")))
        filename = filename or "untitled"
    else:
        filename = "untitled"

    # Ensure unique filename
    output_file = output_dir / f"{filename}.md"
    counter = 1
    while output_file.exists():
        output_file = output_dir / f"{filename}_{counter}.md"
        counter += 1

    # Write markdown file
    output_file.write_text(frontmatter, encoding="utf-8")

    return output_file
