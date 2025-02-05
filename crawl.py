import os
import json
import sys
import time
import random
from urllib.parse import urlparse
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

def get_docs_patterns(url):
    """Get common documentation URL patterns based on the site"""
    common_doc_paths = [
        '/docs/.*',
        '/documentation/.*',
        '/guide/.*',
        '/manual/.*',
        '/reference/.*',
        '/api/.*',
        '/learn/.*',
        '/tutorial/.*',
        '/quickstart/.*',
        '/getting-started/.*',
        '/examples/.*',
        # Add base paths without trailing patterns for sites like React
        '/learn',
        '/docs',
        '/api',
        '/reference',
        '/tutorial'
    ]
    
    # Add site-specific patterns
    domain = urlparse(url).netloc
    if 'readthedocs' in domain:
        common_doc_paths.extend(['/en/.*', '/latest/.*'])
    elif 'github.io' in domain:
        common_doc_paths.append('/.*')
    elif 'react.dev' in domain:  # Special handling for React docs
        common_doc_paths.extend([
            '/learn',
            '/reference',
            '/community',
            '/blog',
            '/.*'  # Include all paths for React docs
        ])
    
    return common_doc_paths

def exponential_backoff(attempt, base_delay=1):
    """Calculate delay with exponential backoff and jitter"""
    delay = min(300, base_delay * (2 ** attempt))  # Cap at 5 minutes
    jitter = delay * 0.1 * (random.random() * 2 - 1)  # ±10% jitter
    return delay + jitter

def retry_with_backoff(func, max_retries=5):
    """Retry a function with exponential backoff"""
    attempt = 0
    while True:
        try:
            return func()
        except Exception as e:
            if "429" in str(e):  # Rate limit error
                if attempt >= max_retries:
                    raise
                delay = exponential_backoff(attempt)
                print(f"Rate limit hit. Waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
                attempt += 1
            else:
                raise

def crawl_docs(url, test_mode=False):
    """
    Crawl documentation pages from a given URL
    
    Args:
        url (str): The base URL to crawl
        test_mode (bool): If True, only crawl up to 10 pages
    """
    # Load environment variables
    load_dotenv()

    # Initialize Firecrawl
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    base_domain = urlparse(url).netloc

    try:
        # First try to scrape the initial URL to get links
        print("Getting initial page links...")
        initial_scrape = retry_with_backoff(
            lambda: app.scrape_url(
                url,
                params={
                    'formats': ['links'],
                    'onlyMainContent': False  # We want all links including nav
                }
            )
        )
        
        # Extract URLs from initial scrape (only internal links)
        initial_urls = [
            u for u in initial_scrape.get('links', [])
            if urlparse(u).netloc == base_domain
        ]
        print(f"\nFound {len(initial_urls)} internal links on initial page:")
        for u in initial_urls[:5]:
            print(f"  - {u}")

        # Then map the site to get all URLs
        print("\nMapping website structure...")
        map_result = retry_with_backoff(
            lambda: app.map_url(
                url,
                params={
                    'ignoreSitemap': True,
                    'includeSubdomains': False,
                    'limit': 10 if test_mode else 1000,
                    'maxDepth': 2 if test_mode else 5,
                    'allowExternalLinks': False,
                    'allowBackwardLinks': True
                }
            )
        )
        
        # Debug the map_result
        print("\nMap result structure:", json.dumps(map_result, indent=2)[:500] + "...")
        
        # Get appropriate doc patterns for this site
        doc_patterns = get_docs_patterns(url)
        print(f"Using doc patterns: {doc_patterns}")
        
        # Combine URLs from both initial scrape and map (only internal links)
        all_urls = set(initial_urls + [
            u for u in map_result.get('links', [])
            if urlparse(u).netloc == base_domain
        ])
        print(f"\nFound {len(all_urls)} total unique internal URLs")
        print("Sample URLs found:")
        for u in list(all_urls)[:5]:
            print(f"  - {u}")
        
        # Filter for documentation URLs using multiple common patterns
        doc_urls = [
            u for u in all_urls
            if any(
                (pattern.endswith('.*') and pattern.rstrip('.*') in urlparse(u.lower()).path) or
                (not pattern.endswith('.*') and pattern == urlparse(u.lower()).path)
                for pattern in doc_patterns
            )
        ]
        
        if not doc_urls:
            print("\nWarning: No documentation pages matched our patterns!")
            print("This might mean we need to adjust our patterns or URL matching logic.")
            doc_urls = list(all_urls)  # Already filtered for internal URLs
            print(f"Falling back to all {len(doc_urls)} internal URLs")
        
        # In test mode, limit to 10 URLs
        if test_mode and len(doc_urls) > 10:
            print("\nTest mode: limiting to 10 URLs")
            doc_urls = sorted(doc_urls)[:10]
        
        print(f"\nFound {len(doc_urls)} documentation pages to crawl:")
        for u in doc_urls:  # Show all in test mode, or first 10 in normal mode
            print(f"  - {u}")
        
        # Crawl all documentation pages
        crawl_status = retry_with_backoff(
            lambda: app.crawl_url(
                url,
                params={
                    'limit': len(doc_urls) + 1,
                    'maxDepth': 2 if test_mode else 5,
                    'includePaths': [urlparse(u).path for u in doc_urls],
                    'excludePaths': [
                        '.*/blog/.*',
                        '.*/legal/.*',
                        '.*/terms/.*'
                    ],
                    'allowBackwardLinks': True,
                    'allowExternalLinks': False,
                    'scrapeOptions': {
                        'formats': ['markdown', 'html'],
                        'onlyMainContent': True,
                        'includeTags': [
                            'article', 'main', '.content', '.documentation',
                            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                            'p', 'ul', 'ol', 'li', 'code', 'pre'
                        ],
                        'excludeTags': [
                            'nav', 'header', 'footer',
                            '.sidebar', '.menu', '.navigation'
                        ],
                        'waitFor': 2000
                    }
                },
                poll_interval=30
            )
        )

        # Save the results to output.json
        with open('output.json', 'w') as f:
            json.dump(crawl_status, f, indent=2)
            
        print("Crawl completed successfully!")
        
    except Exception as e:
        print(f"Error during crawl: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawl.py <docs_url> [--test]")
        sys.exit(1)
    
    test_mode = "--test" in sys.argv
    url = sys.argv[1]
    
    if test_mode:
        print("Running in test mode (max 10 pages)")
    
    crawl_docs(url, test_mode) 