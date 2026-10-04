#!/usr/bin/env python3
"""
PriceHunter — Autonomous Shopping Agent
Finds the cheapest prices for a product using Google Shopping search via SerpAPI.
"""

import os
import sys
import json
import argparse
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)


# ─── Configuration ────────────────────────────────────────────────────────────

SERPAPI_BASE_URL = "https://serpapi.com/search"
DEFAULT_NUM_RESULTS = 10


# ─── Core Functions ───────────────────────────────────────────────────────────

def search_product(product_name: str, api_key: str, num_results: int = DEFAULT_NUM_RESULTS) -> list[dict]:
    """
    Search for a product on Google Shopping via SerpAPI.
    Returns a list of dicts with keys: title, price, url, source.
    """
    params = {
        "engine": "google_shopping",
        "q": product_name,
        "api_key": api_key,
        "num": num_results,
        "hl": "en",
        "gl": "in",
    }

    response = requests.get(SERPAPI_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(f"SerpAPI error: {data['error']}")

    results = []
    for item in data.get("shopping_results", []):
        # Extract price — SerpAPI returns it as a string like "$29.99"
        price_str = item.get("price", "")
        price = parse_price(price_str)

        results.append({
            "title": item.get("title", "N/A"),
            "price": price,
            "price_display": price_str,
            "url": item.get("link", item.get("product_link", "")),
            "source": item.get("source", "N/A"),
        })

    return results


def parse_price(price_str: str) -> Optional[float]:
    """Parse a price string like '₹1,299.99' or '$1,299.99' into a float."""
    if not price_str:
        return None

    # 1. Detect subscription prices (e.g., "/mo", "/month", "per month")
    # We ignore these because they aren't the full purchase price.
    subscription_keywords = ["/mo", "/month", "per month", "monthly", "payment"]
    if any(kw in price_str.lower() for kw in subscription_keywords):
        return None

    # 2. Remove common currency symbols and commas
    # Added ₹ for Indian Rupees
    cleaned = price_str.replace("₹", "").replace("$", "").replace("€", "").replace("£", "").replace(",", "").strip()

    # 3. Extract the numeric portion
    import re
    match = re.search(r"[\d.]+", cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def display_results(results: list[dict], product_name: str) -> None:
    """Display results sorted by price (cheapest first)."""
    if not results:
        print(f"\nNo results found for '{product_name}'.")
        return

    # Sort by price (None prices go last)
    sorted_results = sorted(results, key=lambda x: (x["price"] is None, x["price"] or 0))

    print(f"\n{'='*70}")
    print(f"  PriceHunter results for: {product_name}")
    print(f"{'='*70}")
    print(f"{'#':<4} {'Price':<12} {'Source':<20} {'Title':<30}")
    print(f"{'-'*70}")

    for i, r in enumerate(sorted_results, 1):
        price_str = r["price_display"] if r["price_display"] else "N/A"
        title = r["title"][:28] + ".." if len(r["title"]) > 30 else r["title"]
        source = r["source"][:18] + ".." if len(r["source"]) > 20 else r["source"]
        print(f"{i:<4} {price_str:<12} {source:<20} {title:<30}")

    print(f"{'-'*70}")
    print(f"\nDetailed results (with URLs):")
    print(f"{'='*70}")

    for i, r in enumerate(sorted_results, 1):
        print(f"\n  [{i}] {r['title']}")
        print(f"      Price:  {r['price_display'] or 'N/A'}")
        print(f"      Source: {r['source']}")
        print(f"      URL:    {r['url'] or 'N/A'}")


def save_results(results: list[dict], product_name: str, output_dir: str = ".") -> str:
    """Save results to a JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    safe_name = product_name.replace(" ", "_").lower()[:50]
    filepath = os.path.join(output_dir, f"results_{safe_name}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"query": product_name, "results": results}, f, indent=2, ensure_ascii=False)

    return filepath


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PriceHunter — Find the cheapest prices for any product.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python price_hunter.py "Sony WH-1000XM5"
  python price_hunter.py "iPhone 15 Pro 256GB" --num 20
  python price_hunter.py "Nintendo Switch OLED" --save
        """,
    )
    parser.add_argument("product", help="Product name to search for")
    parser.add_argument("--num", type=int, default=DEFAULT_NUM_RESULTS,
                        help=f"Number of results to fetch (default: {DEFAULT_NUM_RESULTS})")
    parser.add_argument("--save", action="store_true",
                        help="Save results to a JSON file")
    parser.add_argument("--output-dir", default=".",
                        help="Directory to save results (default: current directory)")

    args = parser.parse_args()

    # Get API key from environment variable
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        print("\n" + "=" *70)
        print("  ERROR: SERPAPI_API_KEY environment variable not set!")
        print("="*70)
        print("""
  You need a SerpAPI key to use PriceHunter.

  1. Go to https://serpapi.com/ and sign up (free tier: 100 searches/month)
  2. Copy your API key from the dashboard
  3. Set it as an environment variable:

     export SERPAPI_API_KEY="your_api_key_here"

  Or create a .env file in this directory with:
     SERPAPI_API_KEY=your_api_key_here
""")
        sys.exit(1)

    print(f"\nSearching for: {args.product} ...")

    try:
        results = search_product(args.product, api_key, args.num)
        display_results(results, args.product)

        if args.save:
            filepath = save_results(results, args.product, args.output_dir)
            print(f"\nResults saved to: {filepath}")

    except requests.exceptions.HTTPError as e:
        print(f"\nHTTP Error: {e}")
        if e.response is not None and e.response.status_code == 401:
            print("Your API key may be invalid. Check your SerpAPI dashboard.")
        elif e.response is not None and e.response.status_code == 429:
            print("Rate limit exceeded. Wait a moment or upgrade your SerpAPI plan.")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
