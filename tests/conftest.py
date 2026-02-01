"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return {
        "web": "https://example.com/article",
        "youtube": "https://youtube.com/watch?v=abc123",
        "pdf": "https://example.com/document.pdf",
    }


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """---
url: https://example.com/article
title: Test Article
source: web
---

# Test Article

This is test content.
"""


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
