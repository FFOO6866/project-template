"""
Investigate Horme.com.sg Search Functionality
Find the correct search URL and test with natural language queries

Author: Horme Production Team
Date: 2025-10-22
"""

import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

SCRAPERAPI_KEY = '3c29b7d4798bd49564aacf76ba828d8a'


def fetch_with_scraperapi(url: str, render: bool = False) -> str:
    """Fetch URL using ScraperAPI"""
    proxy_url = "http://api.scraperapi.com"
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': url,
        'render': 'true' if render else 'false'
    }

    try:
        response = requests.get(proxy_url, params=params, timeout=60)
        if response.status_code == 200:
            return response.text
        else:
            print(f"HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def investigate_homepage():
    """Investigate homepage to find search functionality"""
    print("="*80)
    print("INVESTIGATING HORME.COM.SG HOMEPAGE")
    print("="*80)

    url = "https://www.horme.com.sg"
    print(f"\nFetching: {url}")

    html = fetch_with_scraperapi(url)

    if not html:
        print("Failed to fetch homepage")
        return

    print(f"Success! Received {len(html):,} bytes")

    soup = BeautifulSoup(html, 'html.parser')

    # Find search form
    print("\n" + "="*80)
    print("SEARCH FORMS FOUND:")
    print("="*80)

    forms = soup.find_all('form')
    print(f"Total forms found: {len(forms)}")

    for i, form in enumerate(forms, 1):
        action = form.get('action', '')
        method = form.get('method', 'GET')

        # Find search-related inputs
        inputs = form.find_all('input')
        search_inputs = [inp for inp in inputs if 'search' in str(inp).lower()]

        if search_inputs or 'search' in action.lower():
            print(f"\nForm #{i} (LIKELY SEARCH):")
            print(f"  Action: {action}")
            print(f"  Method: {method}")
            print(f"  Inputs:")
            for inp in inputs:
                print(f"    - {inp.get('name', 'unnamed')}: {inp.get('type', 'text')}")

    # Find search links
    print("\n" + "="*80)
    print("SEARCH-RELATED LINKS:")
    print("="*80)

    links = soup.find_all('a', href=True)
    search_links = [link for link in links if 'search' in link['href'].lower()]

    for link in search_links[:10]:
        href = link['href']
        text = link.get_text(strip=True)
        print(f"  {href} -> {text}")

    # Look for search input fields
    print("\n" + "="*80)
    print("SEARCH INPUT FIELDS:")
    print("="*80)

    search_inputs = soup.find_all('input', {'type': 'search'})
    search_inputs += soup.find_all('input', {'placeholder': re.compile('search', re.I)})
    search_inputs += soup.find_all('input', {'name': re.compile('search|query|q', re.I)})

    for inp in search_inputs:
        print(f"  Name: {inp.get('name')}")
        print(f"  Placeholder: {inp.get('placeholder')}")
        print(f"  ID: {inp.get('id')}")
        print()

    # Save HTML for manual inspection
    with open('horme_homepage.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nHomepage HTML saved to: horme_homepage.html")


def test_search_patterns():
    """Test different search URL patterns"""
    print("\n" + "="*80)
    print("TESTING SEARCH URL PATTERNS")
    print("="*80)

    test_queries = [
        "drill",
        "safety helmet",
        "power tools"
    ]

    url_patterns = [
        "https://www.horme.com.sg/search?q={query}",
        "https://www.horme.com.sg/Search?q={query}",
        "https://www.horme.com.sg/search?query={query}",
        "https://www.horme.com.sg/search/{query}",
        "https://www.horme.com.sg/products?search={query}",
        "https://www.horme.com.sg/catalog/search?q={query}",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 40)

        for pattern in url_patterns:
            url = pattern.format(query=query.replace(' ', '+'))
            print(f"  Testing: {url}")

            html = fetch_with_scraperapi(url)

            if html:
                status = "SUCCESS" if len(html) > 5000 else "SMALL RESPONSE"

                # Check if it looks like search results
                soup = BeautifulSoup(html, 'html.parser')
                products = soup.find_all(class_=re.compile('product', re.I))

                print(f"    -> {status} ({len(html):,} bytes, {len(products)} potential products)")

                if len(products) > 0:
                    print(f"    -> FOUND PRODUCTS! This pattern works!")
                    return pattern
            else:
                print(f"    -> FAILED")

        break  # Just test first query

    return None


def main():
    """Main investigation"""
    investigate_homepage()

    working_pattern = test_search_patterns()

    if working_pattern:
        print("\n" + "="*80)
        print("SUCCESS!")
        print("="*80)
        print(f"Working search pattern: {working_pattern}")
    else:
        print("\n" + "="*80)
        print("NO WORKING PATTERN FOUND")
        print("="*80)
        print("Need to manually inspect horme_homepage.html to find search")


if __name__ == "__main__":
    main()
