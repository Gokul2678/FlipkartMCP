# Flipkart MCP Server

A Model Context Protocol (MCP) server for scraping product information from Flipkart.com.

## Features

- **Product Scraping**: Extract detailed product information from Flipkart product URLs
- **Product Search**: Search Flipkart catalog and get product listings
- **No Authentication Required**: Scrapes publicly available product pages

## Tools Provided

### 1. `scrape_product(product_url: str)`

Scrapes detailed product information from a Flipkart product URL.

**Parameters:**
- `product_url` (string): Full URL of the Flipkart product page

**Returns:**
- Product name
- Current price
- Original price (if available)
- Discount percentage
- Product images
- Rating and reviews count
- Availability status
- Product highlights
- Specifications
- Description

**Example:**
```python
scrape_product("https://www.flipkart.com/product-name/p/itm...")
```

### 2. `search_products(query: str, max_results: int = 5)`

Searches for products on Flipkart and returns results.

**Parameters:**
- `query` (string): Search term (e.g., "laptop", "smartphone")
- `max_results` (integer, optional): Maximum number of results to return (default: 5, max: 20)

**Returns:**
List of products with:
- Product name
- Price
- Image URL
- Rating
- Product URL

**Example:**
```python
search_products("smartphone", max_results=10)
```

## Installation

The FlipkartMCP server is automatically installed via the `setup-mcp.ts` script.

### Manual Installation

1. Create directory:
```bash
mkdir -p /tmp/FlipkartMCP
```

2. Create Python virtual environment:
```bash
cd /tmp/FlipkartMCP
python3 -m venv .venv
```

3. Install dependencies:
```bash
.venv/bin/pip install -r requirements.txt
```

4. Run the server:
```bash
.venv/bin/python server.py
```

## Configuration

The server is configured in `.opencode/opencode.jsonc`:

```jsonc
"flipkart-mcp": {
  "type": "local",
  "command": [
    "/tmp/FlipkartMCP/.venv/bin/python",
    "/tmp/FlipkartMCP/server.py"
  ],
  "enabled": true,
  "timeout": 15000
}
```

## Dependencies

- `mcp` - Model Context Protocol framework
- `httpx` - Async HTTP client
- `beautifulsoup4` - HTML parsing
- `python3.14+` - Python runtime

## Technical Details

- **Framework**: FastMCP
- **HTTP Client**: httpx (async)
- **HTML Parser**: BeautifulSoup4
- **User-Agent**: Mimics Chrome browser to avoid blocking

## Implementation Notes

### Robust Scraping Strategy

The implementation follows best practices from [ScrapingDog's Flipkart scraping guide](https://www.scrapingdog.com/blog/scrape-flipkart/):

**1. Anti-Bot Protection**
- Browser-like headers with `Sec-Fetch-*` signals
- Proper `Accept-Language` and `Accept-Encoding` (including Brotli)
- Chrome User-Agent mimicry
- 15-second timeout to avoid triggering rate limits

**2. CSS Selector Strategy**
- Multiple fallback selectors for each data field (5-7 per field)
- Prioritizes semantic HTML (`<h1>` for titles) over class-based selectors
- Structure-based parsing for search results (URL patterns, price symbols)
- Resilient to Flipkart's frequent page structure updates

**3. Product Page Selectors**
- **Name**: `<h1>` tag → class-based fallbacks
- **Price**: `._30jeq3._16Jk6d` → multiple alternatives
- **Highlights**: `ul li._21Ahn-` → generic list selectors
- **Description**: `._1mXcCf.RmoJUa` → single class fallback
- **Images**: Gallery (`li._20Gt85`, `li._1Y_A6W`) → single image fallbacks

**4. Search Results Optimization**
- Uses URL pattern matching (`/p/itm`, `/p/products`) for product links
- Finds product containers via price symbol (`₹`) proximity
- Extracts names from `RG5Slk` class (2025 structure) with fallbacks
- Filters out specifications text (RAM, Processor, etc.)
- De-duplicates results by URL

**5. Error Handling**
- Graceful degradation (returns partial data if some fields missing)
- Descriptive JSON error responses
- HTTP error catching with context
- Timeout protection

## Comparison with Amazon MCP

| Feature | Amazon MCP | Flipkart MCP |
|---------|-----------|--------------|
| Product Details | ✅ | ✅ |
| Search | ✅ | ✅ |
| Price (current) | ✅ | ✅ |
| Price (original) | ❌ | ✅ |
| Discount % | ❌ | ✅ |
| Images | ✅ | ✅ |
| Rating | ✅ | ✅ |
| Reviews | ✅ | ✅ |
| Specifications | ❌ | ✅ |
| Highlights | ❌ | ✅ |
| Availability | ✅ | ✅ |
| Description | ✅ | ✅ |

## Usage in ShopOS

The Flipkart MCP tools can be used by ShopOS agents to:
- Compare prices across marketplaces (Flipkart vs Amazon)
- Analyze product availability
- Research competitor products
- Generate product recommendations
- Create marketplace expansion strategies

## Error Handling

The server handles:
- Invalid URLs
- HTTP errors (404, 500, etc.)
- Parsing failures
- Missing data fields
- Network timeouts

All errors return descriptive JSON error messages.

## License

Similar to the Amazon MCP implementation, this is a custom scraper for internal use.

## Author

Built for ShopOS integration - e-commerce operations agent platform.
