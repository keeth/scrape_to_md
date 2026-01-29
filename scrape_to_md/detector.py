"""URL type detection."""
import re
from urllib.parse import urlparse


def detect_url_type(url: str) -> str:
    """Detect the type of URL for appropriate scraping method.

    Args:
        url: URL to analyze

    Returns:
        One of: 'youtube', 'pdf', 'web'
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    # YouTube detection
    if 'youtube.com' in domain or 'youtu.be' in domain:
        return 'youtube'

    # PDF detection
    if path.endswith('.pdf'):
        return 'pdf'

    # Everything else uses web scraping (Chrome + trafilatura)
    return 'web'
