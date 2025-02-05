import os
import json
import sys
import time
import random
import pathlib
from urllib.parse import urlparse, unquote
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

def sanitize_filename(url):
    """Convert URL path to a safe filename"""
    # Get the path part of the URL and decode any URL encoding
    path = unquote(urlparse(url).path)
    # Remove leading/trailing slashes and replace internal ones with dashes
    filename = path.strip('/').replace('/', '-')
    # If empty (e.g. homepage), use 'index'
    return filename or 'index'

def save_crawl_results(crawl_status, base_domain):
    """Save crawl results to individual files in a domain-specific folder"""
    # Create the docs folder with domain name
    output_dir = pathlib.Path(f"{base_domain}-docs")
    output_dir.mkdir(exist_ok=True)
    
    # Save a manifest file with all URLs and their file mappings
    manifest = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'base_domain': base_domain,
        'pages': {}
    }
    
    # Extract pages from crawl status
    pages = crawl_status.get('pages', {})
    if not pages:
        print("Warning: No pages found in crawl results")
        return
    
    print(f"\nSaving {len(pages)} pages to {output_dir}...")
    
    # Save each page to its own file
    for url, page_data in pages.items():
        if not page_data.get('markdown'):
            print(f"Skipping {url} - no markdown content found")
            continue
            
        # Create a safe filename
        base_filename = sanitize_filename(url)
        
        # Save markdown
        md_file = output_dir / f"{base_filename}.md"
        md_file.write_text(page_data['markdown'])
        manifest['pages'][url] = {
            'markdown_file': str(md_file.relative_to(output_dir)),
            'title': page_data.get('metadata', {}).get('title', ''),
            'description': page_data.get('metadata', {}).get('description', '')
        }
    
    # Save the manifest
    manifest_file = output_dir / 'manifest.json'
    manifest_file.write_text(json.dumps(manifest, indent=2))
    
    print(f"Saved {len(manifest['pages'])} files to {output_dir}")
    print(f"Manifest saved to {manifest_file}")

def normalize_url(url):
    """Normalize URL to use https and remove trailing slashes"""
    parsed = urlparse(url)
    # Force https
    normalized = f"https://{parsed.netloc}{parsed.path}"
    # Remove trailing slash unless it's just the domain
    if normalized.endswith('/') and len(normalized) > 8:
        normalized = normalized.rstrip('/')
    return normalized

def crawl_docs(url, test_mode=False, single_mode=False):
    """
    Crawl documentation pages from a given URL
    
    Args:
        url (str): The base URL to crawl
        test_mode (bool): If True, only crawl up to 10 pages
        single_mode (bool): If True, only crawl the given URL without recursion
    """
    # Load environment variables
    load_dotenv()

    # Initialize Firecrawl
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    base_domain = urlparse(url).netloc
    
    # Normalize input URL
    url = normalize_url(url)

    try:
        # First try to scrape the initial URL
        print("Getting initial page...")
        initial_scrape = retry_with_backoff(
            lambda: app.scrape_url(
                url,
                params={
                    'formats': ['links', 'markdown'],
                    'onlyMainContent': False if not single_mode else True
                }
            )
        )
        
        # In single mode, we only save this page and exit
        if single_mode:
            pages = {
                url: {
                    'markdown': initial_scrape.get('markdown', ''),
                    'metadata': initial_scrape.get('metadata', {})
                }
            }
            save_crawl_results({'pages': pages}, base_domain)
            print("\nSingle page crawl completed!")
            return

        # Extract URLs from initial scrape (only internal links)
        initial_urls = [
            normalize_url(u) for u in initial_scrape.get('links', [])
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
            normalize_url(u) for u in map_result.get('links', [])
            if urlparse(u).netloc == base_domain
        ])
        print(f"\nFound {len(all_urls)} total unique internal URLs")
        print("Sample URLs found:")
        for u in sorted(list(all_urls))[:5]:
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
        
        # Start with the initial page content
        pages = {}
        if initial_scrape.get('markdown'):
            pages[url] = {
                'markdown': initial_scrape.get('markdown', ''),
                'metadata': initial_scrape.get('metadata', {})
            }
        
        # Crawl remaining pages
        for page_url in doc_urls:
            if page_url == url:  # Skip initial URL as we already have it
                continue
                
            print(f"\nCrawling {page_url}...")
            try:
                page_result = retry_with_backoff(
                    lambda: app.scrape_url(
                        page_url,
                        params={
                            'formats': ['markdown'],
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
                    )
                )
                pages[page_url] = {
                    'markdown': page_result.get('markdown', ''),
                    'metadata': page_result.get('metadata', {})
                }
            except Exception as e:
                print(f"Error crawling {page_url}: {str(e)}")
                continue

        # Save results to individual files
        save_crawl_results({'pages': pages}, base_domain)
        print("\nCrawl completed successfully!")
        
    except Exception as e:
        print(f"Error during crawl: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawl.py <docs_url> [--test] [--single]")
        sys.exit(1)
    
    test_mode = "--test" in sys.argv
    single_mode = "--single" in sys.argv
    url = sys.argv[1]
    
    if test_mode:
        print("Running in test mode (max 10 pages)")
    elif single_mode:
        print("Running in single page mode")
    
    crawl_docs(url, test_mode, single_mode) 