"""YouTube scraper using yt-dlp and transcript API."""
import json
import subprocess

import yaml
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID

    Raises:
        ValueError: If video ID cannot be extracted
    """
    # Handle youtu.be format
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[-1].split('?')[0].split('&')[0]

    # Handle youtube.com format
    if 'v=' in url:
        return url.split('v=')[-1].split('&')[0]

    raise ValueError(f"Could not extract video ID from URL: {url}")


def scrape_youtube(url: str) -> str:
    """Scrape YouTube video transcript and metadata.

    Args:
        url: YouTube URL

    Returns:
        Markdown content with frontmatter

    Raises:
        RuntimeError: If scraping fails
    """
    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        raise RuntimeError(str(e))

    # Try to get transcript using the new API
    transcript_text = None
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=('en',))
        # Extract text from snippets
        if hasattr(transcript, 'snippets') and transcript.snippets:
            transcript_text = '\n'.join([snippet.text for snippet in transcript.snippets])
    except Exception:
        # If transcript fails, we'll just leave it as None
        pass

    # Get video metadata using JSON output (more reliable than individual flags)
    try:
        result = subprocess.run(
            ['yt-dlp', '-j', '--skip-download', url],
            capture_output=True,
            text=True,
            check=True
        )
        metadata = json.loads(result.stdout)
        title = metadata.get('title', video_id)
        description = metadata.get('description', '')
        # Format duration as "MM:SS" or "HH:MM:SS"
        duration_sec = metadata.get('duration', 0)
        if duration_sec:
            hours = int(duration_sec // 3600)
            minutes = int((duration_sec % 3600) // 60)
            seconds = int(duration_sec % 60)
            if hours > 0:
                duration = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration = f"{minutes}:{seconds:02d}"
        else:
            duration = ''
        upload_date = metadata.get('upload_date', '')
    except Exception as e:
        # If yt-dlp fails, use fallback values
        title = video_id
        description = ''
        duration = ''
        upload_date = ''

    # Create markdown content with properly escaped YAML frontmatter
    frontmatter = {
        'url': url,
        'title': title,
        'source': 'YouTube',
        'video_id': video_id,
        'duration': duration,
        'upload_date': upload_date,
    }

    yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)

    content = f"""---
{yaml_frontmatter}---

# {title}

**URL**: {url}

## Description

{description}

## Transcript

{transcript_text if transcript_text else '*Transcript not available*'}
"""

    return content
