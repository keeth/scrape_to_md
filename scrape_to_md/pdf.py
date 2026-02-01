"""PDF scraper using docling."""
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

from docling.document_converter import DocumentConverter


def scrape_pdf(url: str) -> str:
    """Scrape PDF and convert to markdown.

    Args:
        url: PDF URL

    Returns:
        Markdown content with frontmatter

    Raises:
        RuntimeError: If scraping fails
    """
    # Download PDF to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        urlretrieve(url, tmp_path)
    except Exception as e:
        raise RuntimeError(f"Failed to download PDF: {e}")

    # Convert with docling
    try:
        converter = DocumentConverter()
        result = converter.convert(str(tmp_path))
        markdown_content = result.document.export_to_markdown()
    except Exception as e:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to convert PDF: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)

    # Add frontmatter
    content = f"""---
url: {url}
source: PDF
---

{markdown_content}
"""

    return content
