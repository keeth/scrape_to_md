"""YouTube scraper using yt-dlp and transcript API."""
import subprocess

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

    # Try to get transcript
    transcript_text = None
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = '\n'.join([entry['text'] for entry in transcript])
    except Exception:
        # If transcript fails, try yt-dlp subtitles
        try:
            result = subprocess.run(
                ['yt-dlp', '--skip-download', '--write-auto-sub', '--sub-format', 'vtt',
                 '--output', '/tmp/%(id)s.%(ext)s', url],
                capture_output=True,
                text=True,
                check=False
            )
            # yt-dlp subtitle extraction is complex, skip for now
        except Exception:
            pass

    # Get video metadata
    try:
        result = subprocess.run(
            ['yt-dlp', '--get-title', '--get-description', '--get-duration',
             '--get-upload-date', url],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        title = lines[0] if len(lines) > 0 else 'Unknown'
        description = lines[1] if len(lines) > 1 else ''
        duration = lines[2] if len(lines) > 2 else ''
        upload_date = lines[3] if len(lines) > 3 else ''
    except Exception:
        title = video_id
        description = ''
        duration = ''
        upload_date = ''

    # Create markdown content
    content = f"""---
url: {url}
title: {title}
source: YouTube
video_id: {video_id}
duration: {duration}
upload_date: {upload_date}
---

# {title}

**URL**: {url}

## Description

{description}

## Transcript

{transcript_text if transcript_text else '*Transcript not available*'}
"""

    return content
