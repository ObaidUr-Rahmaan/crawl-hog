# CrawlHog

A robust Documentation web scraper that effortlessly extracts content from any 3rd-party library docs site. 

Powered by Firecrawl to seamlessly handle dynamic content, JavaScript, and convert everything into pristine markdown.

## Features

- Intelligent docs detection for various documentation formats
- Clean markdown output with proper formatting
- Handles dynamic content and JavaScript-rendered pages
- Supports multiple documentation platforms (standard sites, ReadTheDocs, GitHub Pages)
- Smart content filtering (removes navigation, ads, etc.)
- Site-specific pattern matching
- Progress feedback and error handling
- Rate limit handling with exponential backoff
- Individual file output for each page
- HTML and Markdown formats
- Test mode for quick validation

## Prerequisites

- Python 3.11+
- Firecrawl API key (get it from [firecrawl.dev](https://firecrawl.dev))

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd docs-crawler
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Firecrawl API key:
```bash
FIRECRAWL_API_KEY=your-api-key-here
```

## Usage

### Using the Shell Script (Recommended)

Make the script executable:
```bash
chmod +x chog.sh
```

Then run it with a URL and output folder:
```bash
./chog.sh https://docs.example.com output-folder
```

### Using Python Directly

Run the script with the documentation URL you want to crawl:

```bash
# Full crawl
python crawl.py https://docs.example.com

# Test mode (only crawls up to 10 pages)
python crawl.py https://docs.example.com --test
```

## How It Works

1. **Initial Scrape**
   - Scrapes the initial URL to get all links
   - Filters for internal links only (same domain)

2. **Site Mapping**
   - Maps the entire site structure
   - Discovers all accessible URLs
   - Respects rate limits with exponential backoff

3. **URL Filtering**
   - Matches URLs against common documentation patterns
   - Handles site-specific patterns (React, ReadTheDocs, GitHub Pages)
   - Filters out non-documentation pages

4. **Content Crawling**
   - Crawls each documentation page
   - Extracts both Markdown and HTML content
   - Filters out navigation, ads, and other non-content elements
   - Handles dynamic content with wait times

5. **Output Organization**
   The script creates a folder structure like this:
   ```
   example.com-docs/
   ├── manifest.json         # Contains metadata and file mappings
   ├── index.md             # Homepage in markdown
   ├── quick-start.md       # Other pages in markdown
   ├── api-reference.md
   ├── html/                # HTML versions of the pages
   │   ├── index.html
   │   ├── quick-start.html
   │   └── api-reference.html
   └── ...
   ```

   The `manifest.json` includes:
   - Timestamp of the crawl
   - Base domain
   - URL to file mappings
   - Page metadata (titles, descriptions)

## Rate Limiting

The script handles rate limits gracefully:
- Automatically retries when hitting rate limits
- Uses exponential backoff with jitter
- Shows progress during retries
- Configurable max retries and delays

## Test Mode

Use test mode for quick validation:
```bash
python crawl.py https://docs.example.com --test
```

Test mode:
- Limits crawl to 10 pages maximum
- Uses shallower depth (2 instead of 5)
- Shows all URLs being crawled
- Creates the same folder structure as full mode

## Supported Documentation Patterns

The script recognizes common documentation URL patterns:
- `/docs/*`
- `/documentation/*`
- `/guide/*`
- `/manual/*`
- `/reference/*`
- `/api/*`
- `/learn/*`
- `/tutorial/*`
- `/quickstart/*`
- `/getting-started/*`
- `/examples/*`

Plus site-specific patterns for:
- ReadTheDocs
- GitHub Pages
- React.dev
- And more... 