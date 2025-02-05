"""Command line interface for CrawlHog"""

import os
import click
from ..core.crawler import DocCrawler

@click.group()
@click.version_option()
def cli():
    """CrawlHog - A robust documentation web scraper"""
    pass

@cli.command()
@click.argument('url')
@click.option(
    '-o', '--output',
    help='Output directory (defaults to domain name)',
    type=click.Path()
)
@click.option(
    '--test',
    is_flag=True,
    help='Test mode - only crawl up to 10 pages'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Show detailed progress'
)
@click.option(
    '--api-key',
    help='Firecrawl API key (defaults to FIRECRAWL_API_KEY env var)',
    envvar='FIRECRAWL_API_KEY'
)
def crawl(url, output, test, verbose, api_key):
    """Crawl documentation from a given URL"""
    try:
        crawler = DocCrawler(api_key=api_key)
        output_dir = crawler.crawl(
            url,
            output_dir=output,
            test_mode=test,
            verbose=verbose
        )
        if not verbose:
            click.echo(f"Crawl completed successfully! Results saved to {output_dir}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli() 