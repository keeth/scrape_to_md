# scrape_to_md

Simple URL scraper that outputs markdown files.

## Why this exists

I use agentic scraping workflow with Obsidian, where any resource URL that I quick-add to an inbox note is automatically scraped to Markdown for later reading.

Some of the links I scrape are on Twitter or Substack where a logged in session is necessary. This is problematic for Firecrawl or headless browsers, unless I wanted to store my credentials insecurely and have an agent log in with every scrape.

`scrape_to_md` connects to a head-full browser with a persistent Chrome profile. It sits on your desktop like any other browser, and will store your login sessions between invocations.

In addition to regular web scraping, `scrape_to_md` has special handling for PDFs (docling) and YouTube (transcripts).

For security I recommend not saving raw content in your Obsidian vault, if you have an agent like Claude Code running in the vault, due to risk of prompt injection.  I always use an LLM to summarize any downloaded content that is imported to Obsidian.

This is easily done with Simon Willison's awesome [llm](https://llm.datasette.io/en/stable/):

```
prompt=$(cat <<'EOF'
detailed prose summary of the following text, 
calling out any surprising or interesting details. 
preserve the original markdown frontmatter in your output:
EOF
)

llm -m claude-sonnet-4.5 "$prompt" < $1 > $2
```

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
uv sync --group dev  # Install dev dependencies (pytest, ruff)
playwright install chromium
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=scrape_to_md --cov-report=html

# Run linter
ruff check .

# Format code
ruff format .
```

## Usage

### Quick Start

```bash
# Optional: Create default config file
scrape_to_md init

# Scrape to stdout
scrape_to_md https://example.com/article

# Save to file
scrape_to_md https://example.com/article > article.md

# Scrape a YouTube video
scrape_to_md https://youtube.com/watch?v=abc123 > video.md

# Scrape a PDF
scrape_to_md https://example.com/document.pdf > document.md
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
# Daemon configuration
daemon:
  cdp_port: 9222  # Chrome DevTools Protocol port
  chrome_profile: ~/.local/share/scrape_to_md/chrome_profile
  logs_dir: ~/.local/share/scrape_to_md/logs
  socket_path: ~/.local/share/scrape_to_md/chrome_scraper.sock
```

**Default paths** (used if not specified):
- Chrome profile: `~/.local/share/scrape_to_md/chrome_profile`
- Logs: `~/.local/share/scrape_to_md/logs`
- PID files: `~/.local/share/scrape_to_md/pids`
- Unix socket: `~/.local/share/scrape_to_md/chrome_scraper.sock`

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
