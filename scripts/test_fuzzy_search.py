"""
Test Fuzzy Text Search with Product Descriptions
Uses the autocomplete API and search results page

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import requests
import json
from bs4 import BeautifulSoup

SCRAPERAPI_KEY = '3c29b7d4798bd49564aacf76ba828d8a'


def fetch_with_scraperapi(url: str) -> str:
    """Fetch URL using ScraperAPI"""
    proxy_url = "http://api.scraperapi.com"
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': url,
        'render': 'false'
    }

    try:
        response = requests.get(proxy_url, params=params, timeout=60)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except Exception as e:
        return None


def test_autocomplete(query: str):
    """Test autocomplete API"""
    url = f"https://www.horme.com.sg/ajax_available_keyword_query.aspx?term={query}"
    print(f"\nTesting autocomplete: {url}")

    result = fetch_with_scraperapi(url)

    if result:
        print(f"  SUCCESS! Received: {result[:200]}")
        try:
            data = json.loads(result)
            print(f"  Suggestions: {len(data)} items")
            for item in data[:5]:
                print(f"    - {item}")
        except:
            print(f"  Response: {result}")
    else:
        print(f"  FAILED")


def test_search_page(query: str):
    """Test search results page"""
    # Try different URL patterns
    patterns = [
        f"https://www.horme.com.sg/searchengine.aspx?stq={query}",
        f"https://www.horme.com.sg/searchengine.aspx#stq={query}",
        f"https://www.horme.com.sg/?stq={query}",
    ]

    for url in patterns:
        print(f"\nTesting search page: {url}")

        result = fetch_with_scraperapi(url)

        if result and len(result) > 10000:
            print(f"  SUCCESS! Received {len(result):,} bytes")

            soup = BeautifulSoup(result, 'html.parser')

            # Look for products
            products = soup.find_all(class_=lambda x: x and 'product' in x.lower())
            print(f"  Found {len(products)} potential product elements")

            # Look for prices
            prices = soup.find_all(class_=lambda x: x and 'price' in x.lower())
            print(f"  Found {len(prices)} potential price elements")

            if len(products) > 0 or len(prices) > 0:
                print(f"  *** THIS PATTERN WORKS! ***")
                return url

        else:
            print(f"  Failed or empty response")

    return None


def main():
    """Test with sample product descriptions"""
    print("="*80)
    print("TESTING FUZZY TEXT SEARCH WITH PRODUCT DESCRIPTIONS")
    print("="*80)

    test_queries = [
        "drill",
        "power drill",
        "safety helmet",
        "mobile bin",
        "spray bottle",
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"{'='*80}")

        # Test autocomplete
        test_autocomplete(query)

        # Test search page
        working_url = test_search_page(query)

        if working_url:
            print(f"\n*** FOUND WORKING SEARCH PATTERN: {working_url} ***")
            break


if __name__ == "__main__":
    main()
