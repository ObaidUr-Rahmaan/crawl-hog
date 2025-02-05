"""Core crawler functionality"""

import os
import json
import sys
import time
import random
import pathlib
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# Move all the functions from crawl.py here, but make them more modular
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
        '/learn',
        '/docs',
        '/api',
        '/reference',
        '/tutorial'
    ]
    
    domain = urlparse(url).netloc
    if 'readthedocs' in domain:
        common_doc_paths.extend(['/en/.*', '/latest/.*'])
    elif 'github.io' in domain:
        common_doc_paths.append('/.*')
    elif 'react.dev' in domain:
        common_doc_paths.extend([
            '/learn',
            '/reference',
            '/community',
            '/blog',
            '/.*'
        ])
    
    return common_doc_paths

def exponential_backoff(attempt, base_delay=1):
    """Calculate delay with exponential backoff and jitter"""
    delay = min(300, base_delay * (2 ** attempt))
    jitter = delay * 0.1 * (random.random() * 2 - 1)
    return delay + jitter

def retry_with_backoff(func, max_retries=5):
    """Retry a function with exponential backoff"""
    attempt = 0
    while True:
        try:
            return func()
        except Exception as e:
            if "429" in str(e):
                if attempt >= max_retries:
                    raise
                delay = exponential_backoff(attempt)
                print(f"Rate limit hit. Waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
                attempt += 1
            else:
                raise

def normalize_url(url):
    """Normalize URL to use https and remove trailing slashes"""
    parsed = urlparse(url)
    normalized = f"https://{parsed.netloc}{parsed.path}"
    if normalized.endswith('/') and len(normalized) > 8:
        normalized = normalized.rstrip('/')
    return normalized

def sanitize_filename(url):
    """Convert URL path to a safe filename"""
    path = unquote(urlparse(url).path)
    filename = path.strip('/').replace('/', '-')
    return filename or 'index'

class DocCrawler:
    """Main crawler class that handles the documentation crawling process"""
    
    def __init__(self, api_key=None):
        """Initialize the crawler with optional API key"""
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError("Firecrawl API key is required. Set FIRECRAWL_API_KEY env var or pass it to the constructor.")
        self.app = FirecrawlApp(api_key=self.api_key)
    
    def save_results(self, crawl_status, output_dir):
        """Save crawl results to individual files"""
        output_dir = pathlib.Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)
        
        manifest = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pages': {}
        }
        
        pages = crawl_status.get('pages', {})
        if not pages:
            print("Warning: No pages found in crawl results")
            return
        
        print(f"\nSaving {len(pages)} pages to {output_dir}...")
        
        for url, page_data in pages.items():
            if not page_data.get('markdown') and not page_data.get('html'):
                print(f"Skipping {url} - no content found")
                continue
                
            base_filename = sanitize_filename(url)
            
            if page_data.get('markdown'):
                md_file = output_dir / f"{base_filename}.md"
                md_file.write_text(page_data['markdown'])
                manifest['pages'][url] = {
                    'markdown_file': str(md_file.relative_to(output_dir)),
                    'title': page_data.get('metadata', {}).get('title', ''),
                    'description': page_data.get('metadata', {}).get('description', '')
                }
            
            if page_data.get('html'):
                html_dir = output_dir / 'html'
                html_dir.mkdir(exist_ok=True)
                html_file = html_dir / f"{base_filename}.html"
                html_file.write_text(page_data['html'])
                if url in manifest['pages']:
                    manifest['pages'][url]['html_file'] = str(html_file.relative_to(output_dir))
        
        manifest_file = output_dir / 'manifest.json'
        manifest_file.write_text(json.dumps(manifest, indent=2))
        
        print(f"Saved {len(manifest['pages'])} files to {output_dir}")
        print(f"Manifest saved to {manifest_file}")
    
    def crawl(self, url, output_dir=None, test_mode=False, verbose=False):
        """
        Crawl documentation pages from a given URL
        
        Args:
            url (str): The base URL to crawl
            output_dir (str): Directory to save results (defaults to domain name)
            test_mode (bool): If True, only crawl up to 10 pages
            verbose (bool): If True, show more detailed output
        """
        url = normalize_url(url)
        base_domain = urlparse(url).netloc
        output_dir = output_dir or f"{base_domain}-docs"

        try:
            if verbose:
                print("Getting initial page links...")
            initial_scrape = retry_with_backoff(
                lambda: self.app.scrape_url(
                    url,
                    params={
                        'formats': ['links', 'markdown', 'html'],
                        'onlyMainContent': False
                    }
                )
            )
            
            initial_urls = [
                normalize_url(u) for u in initial_scrape.get('links', [])
                if urlparse(u).netloc == base_domain
            ]
            if verbose:
                print(f"\nFound {len(initial_urls)} internal links on initial page")
                for u in initial_urls[:5]:
                    print(f"  - {u}")

            if verbose:
                print("\nMapping website structure...")
            map_result = retry_with_backoff(
                lambda: self.app.map_url(
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
            
            doc_patterns = get_docs_patterns(url)
            all_urls = set(initial_urls + [
                normalize_url(u) for u in map_result.get('links', [])
                if urlparse(u).netloc == base_domain
            ])
            
            if verbose:
                print(f"\nFound {len(all_urls)} total unique internal URLs")
            
            doc_urls = [
                u for u in all_urls
                if any(
                    (pattern.endswith('.*') and pattern.rstrip('.*') in urlparse(u.lower()).path) or
                    (not pattern.endswith('.*') and pattern == urlparse(u.lower()).path)
                    for pattern in doc_patterns
                )
            ]
            
            if not doc_urls:
                if verbose:
                    print("\nNo documentation pages matched patterns, using all internal URLs")
                doc_urls = list(all_urls)
            
            if test_mode and len(doc_urls) > 10:
                if verbose:
                    print("\nTest mode: limiting to 10 URLs")
                doc_urls = sorted(doc_urls)[:10]
            
            if verbose:
                print(f"\nFound {len(doc_urls)} documentation pages to crawl:")
                for u in doc_urls:
                    print(f"  - {u}")
            
            pages = {}
            if initial_scrape.get('markdown') or initial_scrape.get('html'):
                pages[url] = {
                    'markdown': initial_scrape.get('markdown', ''),
                    'html': initial_scrape.get('html', ''),
                    'metadata': initial_scrape.get('metadata', {})
                }
            
            for page_url in doc_urls:
                if page_url == url:
                    continue
                    
                if verbose:
                    print(f"\nCrawling {page_url}...")
                try:
                    page_result = retry_with_backoff(
                        lambda: self.app.scrape_url(
                            page_url,
                            params={
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
                        )
                    )
                    pages[page_url] = {
                        'markdown': page_result.get('markdown', ''),
                        'html': page_result.get('html', ''),
                        'metadata': page_result.get('metadata', {})
                    }
                except Exception as e:
                    print(f"Error crawling {page_url}: {str(e)}")
                    continue

            self.save_results({'pages': pages}, output_dir)
            if verbose:
                print("\nCrawl completed successfully!")
            
            return output_dir
            
        except Exception as e:
            print(f"Error during crawl: {str(e)}")
            sys.exit(1) 