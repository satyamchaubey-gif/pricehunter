# PriceHunter — Autonomous Shopping Agent

Finds the cheapest prices for any product using Google Shopping search via SerpAPI.

## Setup

1. **Get a SerpAPI key** (free tier: 100 searches/month):
   - Sign up at https://serpapi.com/
   - Copy your API key from the dashboard

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your API key**:
   ```bash
   export SERPAPI_API_KEY="your_api_key_here"
   ```
   Or copy `.env.example` to `.env` and fill in your key.

## Usage

```bash
# Basic search
python price_hunter.py "Sony WH-1000XM5"

# Get more results
python price_hunter.py "iPhone 15 Pro 256GB" --num 20

# Save results to JSON
python price_hunter.py "Nintendo Switch OLED" --save

# Save to a specific directory
python price_hunter.py "MacBook Air M2" --save --output-dir ./results
```

## API Keys Required

| Service | Purpose | Free Tier | Get Key |
|---------|---------|-----------|---------|
| **SerpAPI** | Google Shopping search | 100 searches/month | https://serpapi.com/ |

SerpAPI is the only key needed. It provides structured Google Shopping results including prices, product URLs, and retailer names.

## Output

Results are sorted by price (cheapest first) and include:
- Product title
- Price (parsed and display format)
- Retailer/source name
- Product URL

Use `--save` to export results as JSON for further processing.
