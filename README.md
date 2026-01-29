# scrape-to-md

Simple URL scraper that outputs markdown files.

## Features

- **YouTube**: Extracts transcripts and metadata
- **PDF**: Converts PDFs to markdown using docling
- **Web pages**: Uses Chrome (Playwright) + trafilatura for clean content extraction
- **Daemon mode**: Optional persistent Chrome instance for faster web scraping
- No API keys required (no Firecrawl dependency)

## Installation

```bash
cd ~/src/keeth/scrape_to_md
uv tool install .

# Install Playwright browser binaries (required)
~/.local/share/uv/tools/scrape-to-md/bin/python -m playwright install chromium

# Or for development
uv pip install -e .
playwright install chromium
```

## Usage

### Quick Start

```bash
# Optional: Create default config file
scrape_to_md init

# Scrape a web page
scrape_to_md https://example.com/article

# Scrape a YouTube video
scrape_to_md https://youtube.com/watch?v=abc123

# Scrape a PDF
scrape_to_md https://example.com/document.pdf

# Specify output directory
scrape_to_md https://example.com/page -o ~/my-docs
```

### Daemon Mode (Automatic)

Web scraping automatically launches a daemon in the background for better performance:

```bash
# Scraping will auto-start daemon if not running
scrape_to_md https://example.com/article

# Daemon management commands
scrape_to_md serve              # Start daemon in foreground (for debugging)
scrape_to_md serve --status     # Check daemon status
scrape_to_md serve --stop       # Stop daemon
```

**Daemon features:**
- Automatically launches on first web scrape
- Runs in background (no terminal needed after first scrape)
- Faster scraping (no Chrome startup overhead per request)
- Reuses browser session (authentication persists across scrapes)
- Gracefully falls back to direct scraping if daemon fails

## Configuration

Create a config file with sensible defaults:

```bash
scrape_to_md init
```

This creates `~/.config/scrape_to_md/config.yml` with:

```yaml
# Default output directory
output_dir: ~/Documents/scraped

# Optional daemon configuration
daemon:
  cdp_port: 9222  # Chrome DevTools Protocol port
  chrome_profile: ~/.local/share/scrape_to_md/chrome_profile
  logs_dir: ~/.local/share/scrape_to_md/logs
  socket_path: ~/.local/share/scrape_to_md/chrome_scraper.sock
```

**Default paths** (used if not specified):
- Output: `~/Documents/scraped`
- Chrome profile: `~/.local/share/scrape_to_md/chrome_profile`
- Logs: `~/.local/share/scrape_to_md/logs`
- PID files: `~/.local/share/scrape_to_md/pids`
- Unix socket: `~/.local/share/scrape_to_md/chrome_scraper.sock`

## How it works

1. **URL detection**: Automatically detects YouTube, PDF, or general web pages
2. **YouTube**: Uses `yt-dlp` and `youtube-transcript-api` for transcripts
3. **PDF**: Uses `docling` to convert PDF to markdown
4. **Web**: Automatically uses daemon mode for better performance
   - First scrape launches daemon in background
   - Subsequent scrapes reuse the daemon's persistent Chrome instance
   - Falls back to direct Playwright scraping if daemon fails

### Daemon Architecture

Web scraping uses a client-server architecture over Unix sockets:

- **Auto-start**: First web scrape automatically launches daemon in background
- **Server**: Chrome runs with remote debugging enabled (CDP on port 9222)
- **Communication**: Unix socket at `~/.local/share/scrape_to_md/chrome_scraper.sock`
- **Protocol**: aiohttp web service with `/scrape` and `/health` endpoints
- **Browser**: Persistent Chrome instance with custom profile directory
- **Lifecycle**: Daemon persists across scrapes; manually stop with `scrape_to_md serve --stop`
- **Fallback**: Automatically falls back to direct Playwright if daemon unavailable

The daemon is only used for web scraping. YouTube and PDF scraping always use direct methods.

### Why trafilatura instead of Firecrawl?

- No API key required
- Works offline
- Similar content extraction quality
- Open source and actively maintained
- Specifically designed for extracting main article content from HTML

## Output Format

All scraped content is saved as markdown with YAML frontmatter:

```markdown
---
url: https://example.com/article
title: Article Title
source: web
---

# Article Title

Content here...
```
