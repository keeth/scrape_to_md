"""Tests for URL type detection."""

import pytest

from scrape_to_md.detector import detect_url_type


class TestDetectUrlType:
    """Test URL type detection."""

    def test_youtube_urls(self):
        """Test YouTube URL detection."""
        youtube_urls = [
            "https://youtube.com/watch?v=abc123",
            "https://www.youtube.com/watch?v=xyz789",
            "https://youtu.be/abc123",
            "https://m.youtube.com/watch?v=test",
        ]
        for url in youtube_urls:
            assert detect_url_type(url) == "youtube", f"Failed for {url}"

    def test_pdf_urls(self):
        """Test PDF URL detection."""
        pdf_urls = [
            "https://example.com/document.pdf",
            "https://example.com/file.PDF",
            "https://example.com/path/to/doc.pdf",
        ]
        for url in pdf_urls:
            assert detect_url_type(url) == "pdf", f"Failed for {url}"

    def test_web_urls(self):
        """Test web URL detection."""
        web_urls = [
            "https://example.com",
            "https://example.com/article",
            "https://blog.example.com/post/123",
            "https://example.com/page.html",
        ]
        for url in web_urls:
            assert detect_url_type(url) == "web", f"Failed for {url}"

    def test_edge_cases(self):
        """Test edge cases."""
        # YouTube-like but not YouTube
        assert detect_url_type("https://example.com/youtube/video") == "web"

        # PDF in query string (not extension)
        assert detect_url_type("https://example.com?file=doc.pdf") == "web"
