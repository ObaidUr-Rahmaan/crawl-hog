# CrawlHog

Extract documentation sites into clean markdown files. Handles dynamic content and rate limits automatically.

Built for Cursor users to import third-party library docs into their codebase to use with Composer. A more reliable alternative to Cursor's built-in crawler.

Quickly extract content from a single documentation page or an entire docs site into local markdown files.

```
                                                                 
                                                                 
  [Website]                                                      
     |                                                           
     v                                                           
[FireCrawl API] --> [Extract URLs] --> [Scrape Content]         
     |                                       |                   
     v                                       v                   
[Rate Limiting]                     [GPT-3.5 Cleaning]          
                                           |                     
                                           v                     
                                   [Clean Markdown Files]        
```

## Requirements

- Python 3.11+
- Firecrawl API key (get from https://www.firecrawl.dev/app/api-keys)
- OpenAI API key (get from https://platform.openai.com/api-keys)

## Quick Start

```bash
# Install
pyenv install 3.11.0
pyenv local 3.11.0
git clone git@github.com:ObaidUr-Rahmaan/crawl-hog.git && cd crawl-hog
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Add API keys
echo "FIRECRAWL_API_KEY=your-key-here" > .env  
echo "OPENAI_API_KEY=your-key-here" >> .env

# Run
chmod +x chog.sh
./chog.sh https://docs.example.com output-folder        # Full site
./chog.sh https://docs.example.com/page output --single # Single page
```

## Features

- 📚 Handles any docs site (React, ReadTheDocs, GitHub Pages, etc.)
- 🧹 Clean markdown output via GPT-3.5, no nav/ads/junk
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