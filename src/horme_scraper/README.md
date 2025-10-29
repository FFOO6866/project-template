# Horme Web Scraper

A respectful and robust web scraping framework specifically designed for horme.com.sg. This scraper follows best practices for ethical web scraping and includes comprehensive error handling, rate limiting, and data export capabilities.

## Features

### 🚦 Respectful Scraping
- **Rate limiting**: Max 1 request per 5 seconds (configurable, respects robots.txt)
- **Robots.txt compliance**: Automatically checks and respects robots.txt directives
- **User agent rotation**: Rotates between realistic browser user agents
- **Request headers**: Uses authentic browser headers to avoid detection

### 🔄 Robust Error Handling
- **Exponential backoff**: Intelligent retry logic with exponential backoff
- **Timeout handling**: Configurable connection and request timeouts
- **Graceful degradation**: Continues scraping even if some products fail
- **Comprehensive logging**: Detailed logs of all requests and responses

### 📊 Data Extraction
- **Product search**: Search by keywords or specific SKUs
- **Comprehensive parsing**: Extracts names, prices, descriptions, specifications, images
- **Category detection**: Automatically detects product categories from breadcrumbs
- **Availability status**: Tracks stock availability and brand information

### 💾 Data Export
- **JSON export**: Clean, structured JSON output
- **CSV export**: Optional CSV format for spreadsheet compatibility
- **Session tracking**: Detailed statistics and error reporting
- **Timestamp tracking**: All data includes scraping timestamps

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements-horme-scraper.txt
```

2. The scraper is ready to use!

## Quick Start

### Basic Usage

```python
from horme_scraper import HormeScraper, ScrapingConfig

# Create configuration
config = ScrapingConfig(
    rate_limit_seconds=5.0,  # Respect robots.txt
    max_retries=3,
    output_directory="scraped_data",
    save_json=True
)

# Initialize scraper
scraper = HormeScraper(config)

# Start a scraping session
session_id = scraper.start_session()

# Search for products
product_urls = scraper.search_products("drill", max_results=5)

# Scrape product details
products = scraper.scrape_products(product_urls)

# Save results
scraper.save_products(products, "drill_products")

# End session
session_stats = scraper.end_session()
```

### Search by SKU

```python
# Find a specific product by SKU
product_url = scraper.search_by_sku("ABC123")

if product_url:
    product = scraper.scrape_product(product_url)
    print(f"Found: {product.name} - {product.price}")
```

## CLI Usage

The scraper includes a comprehensive command-line interface:

### Search for products
```bash
python -m horme_scraper.cli search "power tools" --max-results 10
```

### Find product by SKU
```bash
python -m horme_scraper.cli find-sku ABC123
```

### Scrape a specific product
```bash
python -m horme_scraper.cli scrape-product https://horme.com.sg/product/xyz
```

### Search and scrape all results
```bash
python -m horme_scraper.cli scrape-search "drill" --max-results 5 --output drill_results
```

### Scrape multiple SKUs
```bash
python -m horme_scraper.cli scrape-skus SKU1 SKU2 SKU3 --output sku_results
```

### Generate configuration file
```bash
python -m horme_scraper.cli generate-config --output my_config.json
```

### Use custom configuration
```bash
python -m horme_scraper.cli --config-file my_config.json search "tools"
```

## Configuration

The scraper is highly configurable. Create a `ScrapingConfig` object or JSON file:

```python
config = ScrapingConfig(
    # Rate limiting
    rate_limit_seconds=5.0,        # Min seconds between requests
    max_requests_per_hour=600,     # Hourly request limit
    
    # Retry logic
    max_retries=3,                 # Number of retry attempts
    retry_backoff_factor=2.0,      # Exponential backoff multiplier
    retry_base_delay=1.0,          # Base delay for retries
    
    # Timeouts
    request_timeout=30,            # Request timeout in seconds
    connection_timeout=10,         # Connection timeout in seconds
    
    # Features
    rotate_user_agents=True,       # Rotate user agents
    respect_robots_txt=True,       # Check robots.txt compliance
    
    # Logging
    log_level="INFO",              # Logging level
    log_requests=True,             # Log all requests
    log_responses=True,            # Log response info
    
    # Output
    output_directory="scraped_data", # Output directory
    save_json=True,                # Save JSON files
    save_csv=False,                # Save CSV files
)
```

### Configuration File Example

```json
{
  "rate_limit_seconds": 5.0,
  "max_requests_per_hour": 600,
  "max_retries": 3,
  "retry_backoff_factor": 2.0,
  "request_timeout": 30,
  "rotate_user_agents": true,
  "respect_robots_txt": true,
  "log_level": "INFO",
  "output_directory": "scraped_data",
  "save_json": true,
  "save_csv": false
}
```

## Data Structure

### ProductData Model

Each scraped product contains:

```python
{
    "sku": "DRILL001",
    "name": "Professional Power Drill 18V",
    "price": "S$189.99",
    "description": "High-quality cordless drill...",
    "specifications": {
        "Voltage": "18V",
        "Chuck Size": "13mm",
        "Weight": "1.8kg"
    },
    "images": [
        "https://horme.com.sg/images/drill-main.jpg",
        "https://horme.com.sg/images/drill-side.jpg"
    ],
    "categories": ["Tools", "Power Tools", "Drills"],
    "availability": "In Stock",
    "brand": "DeWalt",
    "url": "https://horme.com.sg/product/DRILL001",
    "scraped_at": "2025-01-15T10:30:45.123456"
}
```

### Session Statistics

Each scraping session provides detailed statistics:

```python
{
    "session_id": "horme_scraping_abc123_1642234567",
    "start_time": "2025-01-15T10:00:00",
    "end_time": "2025-01-15T10:15:30",
    "duration_seconds": 930.0,
    "requests_made": 25,
    "successful_requests": 23,
    "failed_requests": 2,
    "products_scraped": 20,
    "success_rate": 0.92,
    "errors": [
        "2025-01-15T10:05:12: Request timeout for product XYZ"
    ]
}
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest src/horme_scraper/test_scraper.py -v

# Run sample scraping test
python src/horme_scraper/test_scraper.py

# Run example usage
python src/horme_scraper/example_usage.py
```

The test suite includes:
- Unit tests for all components
- Integration tests for scraping workflow  
- Mock data tests for parsing logic
- Rate limiting and retry logic tests
- Error handling and session management tests

## Example Output

### JSON Output (`scraped_data/products_20250115_103045.json`)
```json
[
  {
    "sku": "DRILL001",
    "name": "Professional Power Drill 18V",
    "price": "S$189.99",
    "description": "High-quality cordless drill perfect for professionals",
    "specifications": {
      "Voltage": "18V",
      "Chuck Size": "13mm",
      "Weight": "1.8kg",
      "Battery Type": "Li-ion"
    },
    "images": [
      "https://horme.com.sg/images/drill-main.jpg"
    ],
    "categories": ["Tools", "Power Tools", "Drills"],
    "availability": "In Stock",
    "brand": "DeWalt",
    "url": "https://horme.com.sg/product/DRILL001",
    "scraped_at": "2025-01-15T10:30:45.123456"
  }
]
```

### Session Log (`session_horme_scraping_abc123.json`)
```json
{
  "session_id": "horme_scraping_abc123_1642234567",
  "duration_seconds": 125.5,
  "requests_made": 8,
  "successful_requests": 7,
  "failed_requests": 1,
  "products_scraped": 5,
  "success_rate": 0.875,
  "errors": []
}
```

## Best Practices

### 1. Respectful Scraping
- Always use the default rate limiting (5 seconds between requests)
- Monitor robots.txt changes automatically
- Use realistic user agents and headers
- Limit concurrent requests to avoid overloading servers

### 2. Error Handling
- Always wrap scraping in try-catch blocks
- Check session statistics for failed requests
- Review error logs for troubleshooting
- Use retry logic for transient failures

### 3. Data Management
- Save data frequently to avoid loss
- Use timestamps in filenames for organization
- Validate scraped data before processing
- Keep session logs for audit trails

### 4. Performance
- Use reasonable batch sizes (5-20 products)
- Monitor memory usage for large datasets
- Consider using CSV export for very large datasets
- Clean up temporary files and sessions

## Troubleshooting

### Common Issues

**Rate Limiting Errors**
- Increase `rate_limit_seconds` in configuration
- Check if robots.txt has changed
- Verify internet connection stability

**Product Not Found**
- Verify SKU format matches site conventions
- Check if product URL structure has changed
- Try alternative search terms

**Parsing Errors**
- Website structure may have changed
- Check if HTML selectors need updating
- Verify product page loads correctly in browser

**Session Timeouts**
- Increase `request_timeout` in configuration
- Check network connectivity
- Reduce batch sizes for large scraping jobs

### Debug Mode

Enable detailed logging:

```python
config = ScrapingConfig(
    log_level="DEBUG",
    log_requests=True,
    log_responses=True
)
```

This will provide detailed information about:
- All HTTP requests and responses
- HTML parsing steps
- Rate limiting delays
- Retry attempts and backoff logic

## Legal and Ethical Considerations

This scraper is designed to be respectful and ethical:

1. **Robots.txt Compliance**: Automatically checks and respects robots.txt
2. **Rate Limiting**: Implements conservative rate limiting by default
3. **User Agent Transparency**: Uses realistic browser user agents
4. **Error Handling**: Gracefully handles errors without overwhelming servers
5. **Session Management**: Tracks and limits scraping activity

**Important**: Always ensure you have permission to scrape the target website and comply with their terms of service and local laws.

## License

This software is provided as-is for educational and legitimate business purposes. Users are responsible for ensuring compliance with applicable laws and website terms of service.

## Support

For issues, questions, or contributions:

1. Check the test suite for usage examples
2. Review the example usage script
3. Check session logs for error details
4. Ensure configuration is appropriate for your use case