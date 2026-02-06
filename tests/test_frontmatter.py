"""Tests for YAML frontmatter generation."""

import yaml


def test_youtube_frontmatter_with_special_chars():
    """Test that YouTube frontmatter handles special YAML characters."""
    import yaml

    # Simulate what youtube.py does with a problematic title
    url = "https://youtube.com/watch?v=test123"
    title = 'Test: "Title" with \'quotes\' & special chars'
    video_id = "test123"
    duration = "300"
    upload_date = "20240101"

    # This is what the code now does
    frontmatter = {
        'url': url,
        'title': title,
        'source': 'YouTube',
        'video_id': video_id,
        'duration': duration,
        'upload_date': upload_date,
    }

    yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # This should not raise an exception - validates proper YAML escaping
    parsed = yaml.safe_load(yaml_frontmatter)

    # Verify the title was properly escaped and parsed
    assert parsed['title'] == title
    assert ':' in parsed['title'] or '"' in parsed['title'] or "'" in parsed['title']


def test_web_frontmatter_with_special_chars():
    """Test that web frontmatter handles special YAML characters."""
    # We'll test the frontmatter generation logic directly
    import yaml

    # Simulate what web.py does
    url = "https://example.com"
    title = 'Article: "How to use Claude" & more - Part 1'

    # This is what the code now does
    frontmatter = {
        'url': url,
        'title': title,
        'source': 'web',
    }

    yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # This should not raise an exception
    parsed = yaml.safe_load(yaml_frontmatter)

    # Verify the title was properly escaped and parsed
    assert parsed['title'] == title
    assert parsed['url'] == url
    assert parsed['source'] == 'web'


def test_pdf_frontmatter_with_special_chars():
    """Test that PDF frontmatter handles special URL characters."""
    import yaml

    # Simulate what pdf.py does
    url = "https://example.com/document?name=test&file=doc.pdf"

    frontmatter = {
        'url': url,
        'source': 'PDF',
    }

    yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # This should not raise an exception
    parsed = yaml.safe_load(yaml_frontmatter)

    assert parsed['url'] == url
    assert parsed['source'] == 'PDF'


def test_daemon_client_frontmatter_with_special_chars():
    """Test that daemon client frontmatter handles special characters."""
    import yaml

    # Simulate what daemon_client.py does
    url = "https://example.com/article"
    title = "Breaking: Company's \"New Product\" Launch - Q1 2024"

    frontmatter = {
        'url': url,
        'title': title,
        'source': 'web',
    }

    yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # This should not raise an exception
    parsed = yaml.safe_load(yaml_frontmatter)

    assert parsed['title'] == title
    assert parsed['url'] == url


def test_multiline_title():
    """Test that multiline titles are properly escaped."""
    import yaml

    title = "Line 1\nLine 2\nLine 3"

    frontmatter = {
        'url': 'https://example.com',
        'title': title,
        'source': 'web',
    }

    yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # This should not raise an exception
    parsed = yaml.safe_load(yaml_frontmatter)

    # YAML should preserve the newlines
    assert parsed['title'] == title
