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

Run the script with the documentation URL you want to crawl:

```bash
python crawl.py https://docs.example.com
```

The script will:
1. Map the website structure
2. Identify documentation pages
3. Crawl and extract content
4. Save results to `output.json`

## Output

The script generates an `output.json` file containing:
- Markdown content for each page
- HTML content (if requested)
- Page metadata
- Link structure
- Crawl statistics

## Advanced Configuration

The script includes several optimizations:
- Custom tag inclusion/exclusion
- Dynamic content handling
- Timeout settings
- Domain restrictions
- Path filtering

Modify these in the `crawl.py` script if needed. 