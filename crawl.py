import os
import json
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

def get_docs_patterns(url):
    """Get common documentation URL patterns based on the site"""
    common_doc_paths = [
        '/docs/*',
        '/documentation/*',
        '/guide/*',
        '/manual/*',
        '/reference/*',
        '/api/*',
        '/learn/*',
        '/tutorial/*',
        '/quickstart/*',
        '/getting-started/*',
        '/examples/*'
    ]
    
    # Add site-specific patterns
    domain = urlparse(url).netloc
    if 'readthedocs' in domain:
        common_doc_paths.extend(['/en/*', '/latest/*'])
    elif 'github.io' in domain:
        common_doc_paths.append('/*')  # Most GitHub pages are entirely docs
    
    return common_doc_paths

def crawl_docs(url):
    # Load environment variables
    load_dotenv()

    # Initialize Firecrawl
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    try:
        # First map the site to get all URLs
        print("Mapping website structure...")
        map_result = app.map_url(
            url,
            params={
                'ignoreSitemap': False,  # Try using sitemap if available
                'includeSubdomains': True,  # Include docs on subdomains
                'limit': 1000  # Increased limit for larger doc sites
            }
        )
        
        # Get appropriate doc patterns for this site
        doc_patterns = get_docs_patterns(url)
        
        # Filter for documentation URLs using multiple common patterns
        doc_urls = [
            url for url in map_result.get('urls', []) 
            if any(pattern.replace('*', '') in url.lower() for pattern in doc_patterns)
        ]
        
        print(f"Found {len(doc_urls)} documentation pages to crawl")
        
        # Crawl all documentation pages
        crawl_status = app.crawl_url(
            url,
            params={
                'limit': len(doc_urls) + 1,  # +1 for safety
                'maxDepth': 5,  # Reasonable depth for most doc sites
                'scrapeOptions': {
                    'formats': ['markdown', 'html', 'links'],  # Get links for verification
                    'onlyMainContent': True,  # Skip headers/footers
                    'includeTags': [
                        'article', 'main', '.content', '.documentation',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        'p', 'ul', 'ol', 'li', 'code', 'pre',
                        'table', 'th', 'tr', 'td'
                    ],
                    'excludeTags': [
                        'nav', 'header', 'footer',
                        '.sidebar', '.menu', '.navigation',
                        '#toc', '.table-of-contents',
                        '.ads', '.advertisement'
                    ],
                    'waitFor': 2000,  # Wait for dynamic content
                    'timeout': 60000  # Longer timeout for large pages
                },
                'allowedPaths': doc_patterns,
                'excludePaths': [
                    '*/blog/*',
                    '*/legal/*',
                    '*/terms/*',
                    '*/privacy/*',
                    '*/changelog/*',
                    '*/releases/*',
                    '*/community/*',
                    '*/support/*',
                    '*/download/*',
                    '*/install/*',
                    '*/pricing/*'
                ],
                'allowBackwardLinks': True,  # Allow going up in URL hierarchy
                'allowExternalLinks': False  # Stay on same domain
            },
            poll_interval=30
        )

        # Save the results to output.json
        with open('output.json', 'w') as f:
            json.dump(crawl_status, f, indent=2)
            
        print("Crawl completed successfully!")
        
    except Exception as e:
        print(f"Error during crawl: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python crawl.py <docs_url>")
        sys.exit(1)
    
    crawl_docs(sys.argv[1]) 