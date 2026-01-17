#!/usr/bin/env python3
"""
Simple standalone test for Flipkart MCP
Tests connectivity and basic scraping without relying on MCP framework
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import sys


async def test_basic_connectivity():
    """Test 1: Can we reach Flipkart at all?"""
    print("\n" + "="*80)
    print("TEST 1: Basic Connectivity to Flipkart")
    print("="*80)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

    test_url = "https://www.flipkart.com"

    try:
        print(f"Fetching: {test_url}")
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(test_url, headers=headers)

            print(f"✅ Success!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Size: {len(response.text):,} bytes")
            print(f"   Headers: {dict(list(response.headers.items())[:3])}")

            # Check for blocking
            html_lower = response.text.lower()
            if response.status_code == 403:
                print(f"   ❌ HTTP 403 - IP IS BLOCKED")
                return False
            elif response.status_code == 429:
                print(f"   ❌ HTTP 429 - RATE LIMITED")
                return False
            elif "access denied" in html_lower:
                print(f"   ⚠️  'Access Denied' detected - soft block")
                return False
            elif "captcha" in html_lower:
                print(f"   ⚠️  CAPTCHA detected - soft block")
                return False
            elif len(response.text) < 5000:
                print(f"   ⚠️  Response too small - possible block")
                return False
            else:
                print(f"   ✅ Response looks normal - Flipkart is accessible")
                return True

    except httpx.TimeoutException as e:
        print(f"❌ Timeout!")
        print(f"   Error: {str(e)}")
        print(f"   Possible causes: Slow network, firewall blocking")
        return False
    except httpx.ConnectError as e:
        print(f"❌ Connection Error!")
        print(f"   Error: {str(e)}")
        print(f"   Possible causes: Network firewall, DNS issues")
        return False
    except Exception as e:
        print(f"❌ Error!")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        return False


async def test_product_page():
    """Test 2: Can we scrape a product page?"""
    print("\n" + "="*80)
    print("TEST 2: Product Page Scraping")
    print("="*80)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    test_url = "https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm6ac6485c88b79"

    try:
        print(f"Fetching: {test_url}")
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(test_url, headers=headers)

            print(f"   Status Code: {response.status_code}")

            if response.status_code != 200:
                print(f"   ❌ Non-200 status - cannot scrape")
                return False

            # Try to parse
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try to find product name
            product_name = None
            h1 = soup.find('h1')
            if h1:
                product_name = h1.get_text().strip()

            # Try to find price
            price = None
            price_elem = soup.find('div', class_='Nx9bqj')
            if price_elem:
                price = price_elem.get_text().strip()

            print(f"✅ Page loaded and parsed")
            print(f"   Product Name: {product_name if product_name else '❌ Not found'}")
            print(f"   Price: {price if price else '❌ Not found'}")

            if product_name and price:
                print(f"   ✅ Successfully extracted product data")
                return True
            else:
                print(f"   ⚠️  Could not extract data - page structure may have changed")
                return False

    except Exception as e:
        print(f"❌ Error!")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        return False


async def test_search():
    """Test 3: Can we search products?"""
    print("\n" + "="*80)
    print("TEST 3: Product Search")
    print("="*80)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    search_query = "iphone 15"
    test_url = f"https://www.flipkart.com/search?q={search_query.replace(' ', '+')}"

    try:
        print(f"Searching for: '{search_query}'")
        print(f"URL: {test_url}")

        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(test_url, headers=headers)

            print(f"   Status Code: {response.status_code}")

            if response.status_code != 200:
                print(f"   ❌ Non-200 status - search failed")
                return False

            soup = BeautifulSoup(response.text, 'html.parser')

            # Try to find product links
            product_links = soup.find_all('a', href=True)
            product_urls = [a['href'] for a in product_links if '/p/itm' in a['href']]

            print(f"✅ Search page loaded")
            print(f"   Found {len(product_urls)} product links")

            if len(product_urls) > 0:
                print(f"   Sample URLs:")
                for url in product_urls[:3]:
                    print(f"     • {url[:70]}...")
                print(f"   ✅ Search working correctly")
                return True
            else:
                print(f"   ⚠️  No products found - possible blocking or page structure changed")
                return False

    except Exception as e:
        print(f"❌ Error!")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        return False


async def test_different_protocols():
    """Test 4: HTTP/1.1 vs HTTP/2"""
    print("\n" + "="*80)
    print("TEST 4: Protocol Testing (HTTP/1.1 vs HTTP/2)")
    print("="*80)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    test_url = "https://www.flipkart.com"

    # Test HTTP/1.1
    print("\n   Testing HTTP/1.1...")
    try:
        async with httpx.AsyncClient(follow_redirects=True, http2=False, timeout=15.0) as client:
            response = await client.get(test_url, headers=headers)
            print(f"   ✅ HTTP/1.1 - Status: {response.status_code}, Size: {len(response.text):,} bytes")
    except Exception as e:
        print(f"   ❌ HTTP/1.1 - Error: {type(e).__name__}: {str(e)}")

    # Test HTTP/2 (if available)
    print("\n   Testing HTTP/2...")
    try:
        async with httpx.AsyncClient(follow_redirects=True, http2=True, timeout=15.0) as client:
            response = await client.get(test_url, headers=headers)
            print(f"   ✅ HTTP/2 - Status: {response.status_code}, Size: {len(response.text):,} bytes")
    except ImportError:
        print(f"   ⚠️  HTTP/2 not available (h2 package not installed)")
    except Exception as e:
        print(f"   ❌ HTTP/2 - Error: {type(e).__name__}: {str(e)}")


async def main():
    print("="*80)
    print("FLIPKART MCP - SIMPLE CONNECTIVITY TEST")
    print("="*80)
    print("This will test if Flipkart is accessible from this machine")
    print()

    results = []

    # Test 1
    results.append(("Basic Connectivity", await test_basic_connectivity()))
    await asyncio.sleep(2)

    # Test 2
    results.append(("Product Page", await test_product_page()))
    await asyncio.sleep(2)

    # Test 3
    results.append(("Search", await test_search()))
    await asyncio.sleep(2)

    # Test 4
    await test_different_protocols()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        emoji = "✅" if result else "❌"
        print(f"{emoji} {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 SUCCESS! Flipkart is fully accessible from this machine.")
        print("   Your MCP server should work correctly.")
    elif passed == 0:
        print("\n❌ CRITICAL: All tests failed!")
        print("\nYour IP is likely BLOCKED by Flipkart.")
        print("\nPossible causes:")
        print("   • Cloud/datacenter IP range blocked by Flipkart")
        print("   • Too many requests from this IP")
        print("   • Geographic restrictions")
        print("\nSolutions:")
        print("   • Use a residential proxy service")
        print("   • Use VPN with Indian IP address")
        print("   • Contact your hosting provider about IP reputation")
        print("   • Try from a different server/location")
    else:
        print("\n⚠️  PARTIAL: Some tests failed")
        print("   Review individual test results above for details")

    print("="*80)

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
