# CrawlHog 🐗

Extract documentation sites into clean markdown files. Handles dynamic content and rate limits automatically.

Built for Cursor users to import third-party library docs into their codebase to use with Composer. A more reliable alternative to Cursor's built-in crawler.

Quickly extract content from a single documentation page or an entire docs site into local markdown files.

## Quick Start

```bash
# Install
git clone <repo-url> && cd docs-crawler
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Add API key
echo "FIRECRAWL_API_KEY=your-key-here" > .env  # Get key from firecrawl.dev

# Run
chmod +x chog.sh
./chog.sh https://docs.example.com output-folder        # Full site
./chog.sh https://docs.example.com/page output --single # Single page
```

## Features

- 📚 Handles any docs site (React, ReadTheDocs, GitHub Pages, etc.)
- 🧹 Clean markdown output, no nav/ads/junk
- ⚡️ Fast with rate limiting & retries
- 🎯 Smart docs detection
- 🔍 Test mode: `--test` flag crawls max 10 pages

## Output

```
output-folder/
├── manifest.json  # URLs & metadata
├── index.md      # Homepage
└── *.md          # All other pages
```

## Supported URL Patterns

- `/docs/*`, `/documentation/*`
- `/guide/*`, `/manual/*`
- `/reference/*`, `/api/*`
- `/learn/*`, `/tutorial/*`
- `/quickstart/*`, `/getting-started/*`
- `/examples/*`

## Requirements

- Python 3.11+
- Firecrawl API key 