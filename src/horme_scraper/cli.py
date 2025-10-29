"""
Command-line interface for the Horme web scraper.
"""

import click
import json
import os
from typing import List
from datetime import datetime

from .scraper import HormeScraper
from .models import ScrapingConfig
from .utils import setup_logging, get_default_config


@click.group()
@click.option('--config-file', '-c', type=click.Path(exists=True), 
              help='Path to configuration file')
@click.option('--log-level', '-l', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              default='INFO', help='Logging level')
@click.option('--output-dir', '-o', default='scraped_data', 
              help='Output directory for scraped data')
@click.pass_context
def cli(ctx, config_file, log_level, output_dir):
    """Horme.com.sg web scraper CLI tool."""
    
    # Load configuration
    if config_file:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        config = ScrapingConfig(**config_data)
    else:
        config = get_default_config()
    
    # Override with CLI options
    config.log_level = log_level
    config.output_directory = output_dir
    
    # Setup logging
    logger = setup_logging(config)
    
    # Initialize scraper
    scraper = HormeScraper(config)
    
    # Store in context
    ctx.ensure_object(dict)
    ctx.obj['scraper'] = scraper
    ctx.obj['config'] = config
    ctx.obj['logger'] = logger


@cli.command()
@click.argument('query')
@click.option('--max-results', '-n', default=10, help='Maximum number of results')
@click.pass_context
def search(ctx, query, max_results):
    """Search for products by query."""
    scraper = ctx.obj['scraper']
    logger = ctx.obj['logger']
    
    logger.info(f"Searching for: {query}")
    
    session_id = scraper.start_session()
    
    try:
        urls = scraper.search_products(query, max_results)
        
        if urls:
            click.echo(f"Found {len(urls)} products:")
            for i, url in enumerate(urls, 1):
                click.echo(f"{i}. {url}")
        else:
            click.echo("No products found.")
    
    finally:
        scraper.end_session()


@cli.command()
@click.argument('sku')
@click.pass_context
def find_sku(ctx, sku):
    """Find a product by SKU."""
    scraper = ctx.obj['scraper']
    logger = ctx.obj['logger']
    
    logger.info(f"Searching for SKU: {sku}")
    
    session_id = scraper.start_session()
    
    try:
        url = scraper.search_by_sku(sku)
        
        if url:
            click.echo(f"Found product: {url}")
        else:
            click.echo(f"Product with SKU '{sku}' not found.")
    
    finally:
        scraper.end_session()


@cli.command()
@click.argument('url')
@click.option('--output', '-o', help='Output filename (without extension)')
@click.pass_context
def scrape_product(ctx, url, output):
    """Scrape a single product by URL."""
    scraper = ctx.obj['scraper']
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    logger.info(f"Scraping product: {url}")
    
    session_id = scraper.start_session()
    
    try:
        product = scraper.scrape_product(url)
        
        if product:
            click.echo(f"Successfully scraped: {product.name} ({product.sku})")
            
            # Save the product
            if not output:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output = f"product_{product.sku}_{timestamp}"
            
            results = scraper.save_products([product], output)
            
            for format_type, success in results.items():
                if success:
                    click.echo(f"Saved to {format_type.upper()}: {output}.{format_type}")
                else:
                    click.echo(f"Failed to save {format_type.upper()} file", err=True)
        else:
            click.echo("Failed to scrape product.", err=True)
    
    finally:
        scraper.end_session()


@cli.command()
@click.argument('query')
@click.option('--max-results', '-n', default=10, help='Maximum number of search results')
@click.option('--output', '-o', help='Output filename (without extension)')
@click.pass_context
def scrape_search(ctx, query, max_results, output):
    """Search for products and scrape all results."""
    scraper = ctx.obj['scraper']
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    logger.info(f"Searching and scraping products for: {query}")
    
    session_id = scraper.start_session()
    
    try:
        # Search for products
        urls = scraper.search_products(query, max_results)
        
        if not urls:
            click.echo("No products found for the search query.")
            return
        
        click.echo(f"Found {len(urls)} products. Starting to scrape...")
        
        # Scrape products
        products = scraper.scrape_products(urls)
        
        if products:
            click.echo(f"Successfully scraped {len(products)} products.")
            
            # Save products
            if not output:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_query = safe_query.replace(' ', '_')
                output = f"search_{safe_query}_{timestamp}"
            
            results = scraper.save_products(products, output)
            
            for format_type, success in results.items():
                if success:
                    filename = f"{output}.{format_type}"
                    filepath = os.path.join(config.output_directory, filename)
                    click.echo(f"Saved to {format_type.upper()}: {filepath}")
                else:
                    click.echo(f"Failed to save {format_type.upper()} file", err=True)
        else:
            click.echo("No products were successfully scraped.", err=True)
    
    finally:
        session_stats = scraper.end_session()
        if session_stats:
            click.echo("\nSession Statistics:")
            click.echo(f"  Duration: {session_stats.get('duration_seconds', 0):.2f} seconds")
            click.echo(f"  Requests made: {session_stats['requests_made']}")
            click.echo(f"  Success rate: {session_stats['success_rate']:.2%}")
            click.echo(f"  Products scraped: {session_stats['products_scraped']}")


@cli.command()
@click.argument('skus', nargs=-1, required=True)
@click.option('--output', '-o', help='Output filename (without extension)')
@click.pass_context
def scrape_skus(ctx, skus, output):
    """Scrape products by their SKUs."""
    scraper = ctx.obj['scraper']
    config = ctx.obj['config']
    logger = ctx.obj['logger']
    
    logger.info(f"Scraping {len(skus)} SKUs: {', '.join(skus)}")
    
    session_id = scraper.start_session()
    
    try:
        products = []
        found_urls = []
        
        # Find URLs for each SKU
        for sku in skus:
            click.echo(f"Searching for SKU: {sku}")
            url = scraper.search_by_sku(sku)
            if url:
                found_urls.append(url)
                click.echo(f"  Found: {url}")
            else:
                click.echo(f"  Not found: {sku}", err=True)
        
        if not found_urls:
            click.echo("No products found for any of the provided SKUs.")
            return
        
        click.echo(f"\nScraping {len(found_urls)} products...")
        
        # Scrape products
        products = scraper.scrape_products(found_urls)
        
        if products:
            click.echo(f"Successfully scraped {len(products)} products.")
            
            # Save products
            if not output:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output = f"skus_{timestamp}"
            
            results = scraper.save_products(products, output)
            
            for format_type, success in results.items():
                if success:
                    filename = f"{output}.{format_type}"
                    filepath = os.path.join(config.output_directory, filename)
                    click.echo(f"Saved to {format_type.upper()}: {filepath}")
                else:
                    click.echo(f"Failed to save {format_type.upper()} file", err=True)
        else:
            click.echo("No products were successfully scraped.", err=True)
    
    finally:
        session_stats = scraper.end_session()
        if session_stats:
            click.echo("\nSession Statistics:")
            click.echo(f"  Duration: {session_stats.get('duration_seconds', 0):.2f} seconds")
            click.echo(f"  Requests made: {session_stats['requests_made']}")
            click.echo(f"  Success rate: {session_stats['success_rate']:.2%}")
            click.echo(f"  Products scraped: {session_stats['products_scraped']}")


@cli.command()
@click.option('--output', '-o', default='config.json', help='Output configuration file')
@click.pass_context
def generate_config(ctx, output):
    """Generate a sample configuration file."""
    config = get_default_config()
    
    config_dict = config.to_dict()
    
    # Add comments as a separate dictionary
    config_with_comments = {
        "_comments": {
            "rate_limit_seconds": "Minimum seconds between requests (respects robots.txt)",
            "max_requests_per_hour": "Maximum requests per hour limit",
            "max_retries": "Number of retry attempts for failed requests",
            "retry_backoff_factor": "Exponential backoff multiplier for retries",
            "request_timeout": "Request timeout in seconds",
            "rotate_user_agents": "Whether to rotate user agents",
            "respect_robots_txt": "Whether to respect robots.txt rules",
            "output_directory": "Directory to save scraped data",
            "save_json": "Save data in JSON format",
            "save_csv": "Save data in CSV format"
        },
        **config_dict
    }
    
    try:
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(config_with_comments, f, indent=2, ensure_ascii=False)
        
        click.echo(f"Configuration file generated: {output}")
        click.echo("Edit this file to customize scraping behavior.")
        
    except Exception as e:
        click.echo(f"Error generating configuration file: {e}", err=True)


if __name__ == '__main__':
    cli()