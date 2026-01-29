"""PDF scraper using docling."""
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

from docling.document_converter import DocumentConverter


def scrape_pdf(url: str, output_dir: Path) -> Path:
    """Scrape PDF and convert to markdown.

    Args:
        url: PDF URL
        output_dir: Directory to save output

    Returns:
        Path to output markdown file

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

    # Save to file
    # Get base filename from URL
    base_filename = url.split('/')[-1].replace('.pdf', '').replace('.PDF', '')
    # Sanitize filename: replace filesystem-unfriendly characters (including spaces) with underscore
    safe_filename = "".join(c if c.isalnum() else "_" for c in base_filename[:50])
    # Remove leading/trailing underscores and collapse multiple underscores
    safe_filename = "_".join(filter(None, safe_filename.split("_")))
    filename = f"{safe_filename or 'document'}.md"

    # Ensure unique filename
    output_file = output_dir / filename
    counter = 1
    while output_file.exists():
        output_file = output_dir / f"{safe_filename or 'document'}_{counter}.md"
        counter += 1

    output_file.write_text(content)

    return output_file
