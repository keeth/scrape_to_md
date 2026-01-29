"""Web scraper using Playwright + trafilatura."""
import asyncio
from pathlib import Path

import trafilatura
from playwright.async_api import async_playwright


async def scrape_web(url: str, output_dir: Path) -> Path:
    """Scrape web page using Chrome and extract main content with trafilatura.

    Args:
        url: Web page URL
        output_dir: Directory to save output

    Returns:
        Path to output markdown file

    Raises:
        RuntimeError: If scraping fails
    """
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to URL
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Get page content and title
            html_content = await page.content()
            title = await page.title()

            await browser.close()

    except Exception as e:
        raise RuntimeError(f"Failed to fetch page with Playwright: {e}")

    # Extract main content with trafilatura
    try:
        extracted = trafilatura.extract(
            html_content,
            output_format='markdown',
            include_links=True,
            include_images=True,
            url=url
        )

        if not extracted:
            # Fallback to basic extraction
            extracted = trafilatura.extract(
                html_content,
                output_format='txt',
                url=url
            )

    except Exception as e:
        raise RuntimeError(f"Failed to extract content with trafilatura: {e}")

    if not extracted:
        raise RuntimeError("No content could be extracted from the page")

    # Create markdown with frontmatter
    content = f"""---
url: {url}
title: {title}
source: web
---

# {title}

{extracted}
"""

    # Save to file
    # Sanitize filename: replace filesystem-unfriendly characters (including spaces) with underscore
    safe_title = "".join(c if c.isalnum() else "_" for c in title[:50])
    # Remove leading/trailing underscores and collapse multiple underscores
    safe_title = "_".join(filter(None, safe_title.split("_")))
    filename = f"{safe_title or 'untitled'}.md"

    # Ensure unique filename
    output_file = output_dir / filename
    counter = 1
    while output_file.exists():
        output_file = output_dir / f"{safe_title or 'untitled'}_{counter}.md"
        counter += 1

    output_file.write_text(content)

    return output_file
