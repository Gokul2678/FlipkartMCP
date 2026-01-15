#!/usr/bin/env python3
"""
Flipkart Product Scraper MCP Server
Provides tools to scrape product information and search products on Flipkart
"""

from mcp.server.fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup
import json
from typing import Optional
import re

# Initialize FastMCP server
mcp = FastMCP("Flipkart Product Scraper")


async def fetch_flipkart_page(url: str) -> str:
    """Helper function to fetch Flipkart product page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()
        return response.text


def clean_price(price_text: str) -> str:
    """Clean and format price text"""
    if not price_text:
        return "Price not available"

    # Remove extra whitespace and symbols
    price = re.sub(r'\s+', ' ', price_text.strip())
    # Extract numeric price
    price_match = re.search(r'₹[\d,]+', price)
    if price_match:
        return price_match.group(0)
    return price


def extract_product_data(html_content: str, url: str) -> dict:
    """Extract product information from Flipkart page HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')

    product_data = {
        'name': 'Product name not found',
        'price': 'Price not available',
        'original_price': None,
        'discount': None,
        'image_url': 'No image available',
        'rating': 'No rating',
        'reviews_count': 'No reviews',
        'availability': 'Unknown',
        'description': 'No description available',
        'specifications': [],
        'highlights': [],
        'url': url
    }

    # Extract product name - multiple selector fallbacks
    name_selectors = [
        'span.VU-ZEz',           # Common product title class
        'span.B_NuCI',           # Alternative title class
        'h1.yhB1nd',             # H1 title
        'h1 span',               # Generic H1 span
        '.B_NuCI',
    ]

    for selector in name_selectors:
        name_elem = soup.select_one(selector)
        if name_elem:
            product_data['name'] = name_elem.get_text().strip()
            break

    # Extract price - multiple selector fallbacks
    price_selectors = [
        'div.Nx9bqj.CxhGGd',     # Current price
        'div._30jeq3',           # Alternative price class
        'div._16Jk6d',           # Another price class
        '.Nx9bqj',
    ]

    for selector in price_selectors:
        price_elem = soup.select_one(selector)
        if price_elem:
            product_data['price'] = clean_price(price_elem.get_text())
            break

    # Extract original price (for discount calculation)
    original_price_selectors = [
        'div.yRaY8j.A6+E6v',     # Original price (strikethrough)
        'div._3I9_wc',           # Alternative original price
    ]

    for selector in original_price_selectors:
        original_price_elem = soup.select_one(selector)
        if original_price_elem:
            product_data['original_price'] = clean_price(original_price_elem.get_text())
            break

    # Extract discount percentage
    discount_selectors = [
        'div.UkUFwK span',       # Discount percentage
        '._3Ay6Sb',              # Alternative discount class
    ]

    for selector in discount_selectors:
        discount_elem = soup.select_one(selector)
        if discount_elem:
            discount_text = discount_elem.get_text().strip()
            if '%' in discount_text:
                product_data['discount'] = discount_text
                break

    # Extract image URL
    image_selectors = [
        'img._0DkuPH',           # Product image class
        'img._2r_T1I',           # Alternative image class
        'img[class*="DByuf4"]',  # Another image class pattern
        'div._1YokD2 img',       # Image in container
        'img[alt]',              # Any image with alt text
    ]

    for selector in image_selectors:
        img_elem = soup.select_one(selector)
        if img_elem and img_elem.get('src'):
            img_src = img_elem.get('src')
            # Prefer higher quality images
            if img_src and not img_src.endswith('.gif'):
                product_data['image_url'] = img_src
                break

    # Extract rating
    rating_selectors = [
        'div._3LWZlK',           # Rating value
        'div.XQDdHH',            # Alternative rating
        'span._1lRcqv',          # Another rating class
    ]

    for selector in rating_selectors:
        rating_elem = soup.select_one(selector)
        if rating_elem:
            rating_text = rating_elem.get_text().strip()
            if rating_text and rating_text[0].isdigit():
                product_data['rating'] = f"{rating_text} out of 5"
                break

    # Extract reviews count
    reviews_selectors = [
        'span._2_R_DZ',          # Reviews count
        'span.row > span',       # Alternative reviews
    ]

    for selector in reviews_selectors:
        reviews_elem = soup.select_one(selector)
        if reviews_elem:
            reviews_text = reviews_elem.get_text().strip()
            # Look for patterns like "1,234 Ratings" or "234 Reviews"
            if any(keyword in reviews_text for keyword in ['Rating', 'Review', '&']):
                product_data['reviews_count'] = reviews_text
                break

    # Extract availability
    availability_indicators = [
        ('button._2KpZ6l._2U9uOA', 'Available'),  # Add to cart button
        ('div._16FRp0', 'In Stock'),
        ('div._3xgqrA', 'Out of Stock'),
    ]

    for selector, status in availability_indicators:
        avail_elem = soup.select_one(selector)
        if avail_elem:
            button_text = avail_elem.get_text().strip().upper()
            if 'ADD TO CART' in button_text or 'BUY NOW' in button_text:
                product_data['availability'] = 'In Stock'
            elif 'OUT OF STOCK' in button_text or 'NOTIFY' in button_text:
                product_data['availability'] = 'Out of Stock'
            break

    # Extract product highlights
    highlights_selectors = [
        'ul._1_Bfqy li',         # Highlights list
        'div._2418kt li',        # Alternative highlights
    ]

    for selector in highlights_selectors:
        highlights = soup.select(selector)
        if highlights:
            product_data['highlights'] = [h.get_text().strip() for h in highlights]
            break

    # Extract specifications
    spec_rows = soup.select('div._2GjhP6 tr, table.tbg7Hw tr')
    if spec_rows:
        for row in spec_rows:
            cols = row.find_all(['td', 'th'])
            if len(cols) >= 2:
                key = cols[0].get_text().strip()
                value = cols[1].get_text().strip()
                if key and value:
                    product_data['specifications'].append(f"{key}: {value}")

    # Extract description
    description_selectors = [
        'div._1mXcCf',           # Description container
        'div.qnrGsz',            # Alternative description
        'p._2o5hS8',             # Description paragraph
    ]

    for selector in description_selectors:
        desc_elem = soup.select_one(selector)
        if desc_elem:
            desc_text = desc_elem.get_text().strip()
            if len(desc_text) > 20:  # Avoid short/empty descriptions
                product_data['description'] = desc_text[:500]  # Limit length
                break

    return product_data


def extract_search_results(html_content: str, max_results: int) -> list:
    """Extract search results from Flipkart search page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []

    # Find product containers - UPDATED FOR 2025 STRUCTURE
    # Try new structure first (2025), then fall back to old selectors
    product_selectors = [
        'div.jIjQ8S',            # NEW: 2025 product card container
        'div._1AtVbE',           # OLD: Product card container
        'div._2kHMtA',           # OLD: Alternative product container
        'div.cPHDOP',            # OLD: Another container pattern
        'a._1fQZEK',             # OLD: Product link container
    ]

    product_elements = []
    for selector in product_selectors:
        product_elements = soup.select(selector)
        if product_elements:
            break

    for idx, product in enumerate(product_elements[:max_results]):
        try:
            product_info = {
                'name': 'Name not found',
                'price': 'Price not available',
                'image_url': 'No image',
                'rating': 'No rating',
                'url': 'URL not found'
            }

            # Extract product name - NEW structure uses a.k7wcnx
            name_elem = product.select_one('a.k7wcnx, a.IRpwTa, a.s1Q9rs, div.IRpwTa, div._4rR01T')
            if name_elem:
                name_text = name_elem.get_text().strip()
                # Remove "Add to Compare" prefix if present
                name_text = name_text.replace('Add to Compare', '').strip()
                product_info['name'] = name_text

            # Extract price - NEW structure uses div.hZ3P6w.DeU9vF or div.hZ3P6w
            price_elem = product.select_one('div.hZ3P6w.DeU9vF, div.hZ3P6w, div._30jeq3, div.Nx9bqj, div._1_WHN1')
            if price_elem:
                product_info['price'] = clean_price(price_elem.get_text())

            # Extract image - NEW structure uses img.UCc1lI
            img_elem = product.select_one('img.UCc1lI, img')
            if img_elem and img_elem.get('src'):
                img_src = img_elem.get('src')
                # Skip placeholder/loading images
                if img_src and not img_src.startswith('data:image'):
                    product_info['image_url'] = img_src

            # Extract rating - NEW structure uses div.a7saXW
            rating_elem = product.select_one('div.a7saXW, div._3LWZlK, span._1lRcqv')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                # Extract just the rating number (e.g., "4.2" from "4.21,200 Ratings&62 Reviews")
                if rating_text and rating_text[0].isdigit():
                    # Try to extract the numeric rating with decimal point
                    # Match patterns like "4.2", "4.21", "42" followed by non-digit
                    rating_match = re.match(r'(\d)\.?(\d)?', rating_text)
                    if rating_match:
                        if rating_match.group(2):
                            # Has decimal part
                            product_info['rating'] = f"{rating_match.group(1)}.{rating_match.group(2)}/5"
                        else:
                            # No decimal part
                            product_info['rating'] = f"{rating_match.group(1)}/5"
                    else:
                        product_info['rating'] = rating_text[:20]  # Limit length

            # Extract product URL - NEW structure uses a.k7wcnx for product link
            link_elem = product.select_one('a.k7wcnx, a')
            if not link_elem:
                link_elem = product.find_parent('a')

            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('/'):
                    product_info['url'] = f"https://www.flipkart.com{href}"
                elif href.startswith('http'):
                    product_info['url'] = href

            products.append(product_info)

        except Exception as e:
            continue

    return products


@mcp.tool()
async def scrape_product(product_url: str) -> str:
    """
    Scrape detailed product information from a Flipkart product URL

    Args:
        product_url: The full URL of the Flipkart product page

    Returns:
        Formatted product information including name, price, images, ratings, and more
    """
    try:
        # Validate URL
        if not product_url.startswith('http'):
            return json.dumps({
                'error': 'Invalid URL. Please provide a full Flipkart product URL starting with http:// or https://'
            }, indent=2)

        if 'flipkart.com' not in product_url.lower():
            return json.dumps({
                'error': 'This tool only works with Flipkart product URLs'
            }, indent=2)

        # Fetch and parse the page
        html_content = await fetch_flipkart_page(product_url)
        product_data = extract_product_data(html_content, product_url)

        # Format the output
        output = f"""
Product Information:
-------------------
Name: {product_data['name']}
Price: {product_data['price']}
"""

        if product_data['original_price']:
            output += f"Original Price: {product_data['original_price']}\n"

        if product_data['discount']:
            output += f"Discount: {product_data['discount']}\n"

        output += f"""Rating: {product_data['rating']}
Reviews: {product_data['reviews_count']}
Availability: {product_data['availability']}

Image: {product_data['image_url']}

"""

        if product_data['highlights']:
            output += "Highlights:\n"
            for highlight in product_data['highlights']:
                output += f"  • {highlight}\n"
            output += "\n"

        if product_data['specifications']:
            output += "Specifications:\n"
            for spec in product_data['specifications'][:10]:  # Limit to top 10
                output += f"  • {spec}\n"
            output += "\n"

        output += f"Description: {product_data['description']}\n\n"
        output += f"Product URL: {product_data['url']}"

        return output

    except httpx.HTTPError as e:
        return json.dumps({
            'error': f'Failed to fetch product page: {str(e)}'
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'error': f'Error scraping product: {str(e)}'
        }, indent=2)


@mcp.tool()
async def search_products(query: str, max_results: int = 5) -> str:
    """
    Search for products on Flipkart and return results

    Args:
        query: Search term (e.g., "laptop", "smartphone", "shoes")
        max_results: Maximum number of results to return (default: 5, max: 20)

    Returns:
        List of products matching the search query
    """
    try:
        # Validate parameters
        if not query or len(query.strip()) == 0:
            return json.dumps({
                'error': 'Search query cannot be empty'
            }, indent=2)

        if max_results > 20:
            max_results = 20
        elif max_results < 1:
            max_results = 5

        # Construct search URL
        search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"

        # Fetch and parse search results
        html_content = await fetch_flipkart_page(search_url)
        products = extract_search_results(html_content, max_results)

        if not products:
            return json.dumps({
                'message': f'No products found for query: {query}',
                'search_url': search_url
            }, indent=2)

        # Format output
        output = f"Search Results for '{query}':\n"
        output += f"Found {len(products)} product(s)\n"
        output += "=" * 50 + "\n\n"

        for idx, product in enumerate(products, 1):
            output += f"{idx}. {product['name']}\n"
            output += f"   Price: {product['price']}\n"
            output += f"   Rating: {product['rating']}\n"
            output += f"   Image: {product['image_url']}\n"
            output += f"   URL: {product['url']}\n"
            output += "\n"

        return output

    except httpx.HTTPError as e:
        return json.dumps({
            'error': f'Failed to perform search: {str(e)}'
        }, indent=2)
    except Exception as e:
        return json.dumps({
            'error': f'Error searching products: {str(e)}'
        }, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
