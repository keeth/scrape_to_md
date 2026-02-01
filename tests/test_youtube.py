"""Tests for YouTube scraper."""

import pytest

from scrape_to_md.youtube import extract_video_id


class TestExtractVideoId:
    """Test YouTube video ID extraction."""

    def test_standard_youtube_url(self):
        """Test standard youtube.com URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_youtube_url(self):
        """Test youtu.be short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_youtube_url_with_params(self):
        """Test YouTube URL with additional parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url_with_params(self):
        """Test short URL with parameters."""
        url = "https://youtu.be/dQw4w9WgXcQ?t=42"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_mobile_youtube_url(self):
        """Test mobile YouTube URL."""
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        """Test invalid URL raises ValueError."""
        with pytest.raises(ValueError):
            extract_video_id("https://example.com/not-youtube")

    def test_missing_video_id(self):
        """Test URL without video ID raises ValueError."""
        with pytest.raises(ValueError):
            extract_video_id("https://youtube.com")
