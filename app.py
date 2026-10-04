import os
import asyncio
import logging
from dotenv import load_dotenv

# CRITICAL: Load environment variables BEFORE any other imports that might use them
load_dotenv()

import logging
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pricehunter import search_product
from automation import ShoppingBot
from brain import get_best_deal
from celesto import Computer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PriceHunter")

app = Flask(__name__)
CORS(app)

# --- Celesto Sandbox Configuration ---
# We read these once at startup
CELESTO_API_KEY = os.environ.get("CELESTO_API_KEY")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")

# DEBUG: Print keys to terminal so we know they are loaded (remove in production)
print(f"--- SYSTEM CHECK ---")
print(f"SerpAPI Key Loaded: {'✅' if SERPAPI_API_KEY else '❌'}")
print(f"Celesto Key Loaded: {'✅' if CELESTO_API_KEY else '❌'}")
print(f"-------------------")

celesto_computer = None

def get_celesto_computer():
    """Initialize or return the existing Celesto Cloud Computer."""
    global celesto_computer

    if celesto_computer is not None:
        try:
            celesto_computer.run("echo 1")
        except Exception:
            logger.info("Cloud computer was deleted or timed out. Re-creating...")
            celesto_computer = None

    if celesto_computer is None:
        if not CELESTO_API_KEY:
            raise RuntimeError("CRITICAL ERROR: CELESTO_API_KEY is missing from environment!")

        logger.info("Creating new Celesto Cloud Computer...")
        celesto_computer = Computer(api_key=CELESTO_API_KEY, provider="cloud")
        celesto_computer.start()

        logger.info("Installing Playwright and Chromium in sandbox...")
        celesto_computer.run("pip install playwright")
        celesto_computer.run("playwright install chromium")

    return celesto_computer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    product = request.args.get('q')
    num = request.args.get('num', default=10, type=int)

    if not product:
        return jsonify({"error": "Product name is required"}), 400

    if not SERPAPI_API_KEY:
        return jsonify({"error": "SerpAPI key is missing from server config"}), 500

    try:
        results = search_product(product, SERPAPI_API_KEY, num)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auto-hunt', methods=['POST'])
def auto_hunt():
    data = request.json
    product = data.get('q')

    if not product:
        return jsonify({"error": "Product name is required"}), 400

    try:
        if not SERPAPI_API_KEY:
            return jsonify({"error": "SerpAPI key is missing"}), 500

        results = search_product(product, SERPAPI_API_KEY, 10)

        if not results:
            return jsonify({"error": "Could not find any deals for this product"}), 404

        sorted_results = sorted(results, key=lambda x: (x["price"] is None, x["price"] or 0))
        cheapest = sorted_results[0]

        url = cheapest['url']
        price = cheapest['price_display']
        source = cheapest['source']
        title = cheapest['title']

        computer = get_celesto_computer()
        with open("automation.py", "r") as f:
            script_content = f.read()
        computer.run(f"cat << 'EOF' > automation.py\n{script_content}\nEOF")

        result_output = computer.run(f"python3 automation.py '{url}'")

        if "Item added to cart successfully!" in result_output["stdout"]:
            return jsonify({
                "status": "success",
                "message": f"Mission Accomplished! I found the cheapest {title} at {source} for {price} and added it to your cart."
            })
        else:
            return jsonify({
                "status": "failed",
                "message": f"Found it at {source} for {price}, but I couldn't add it to the cart automatically. Try here: {url}"
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        computer = get_celesto_computer()
        with open("automation.py", "r") as f:
            script_content = f.read()
        computer.run(f"cat << 'EOF' > automation.py\n{script_content}\nEOF")
        result_output = computer.run(f"python3 automation.py '{url}'")

        if "Item added to cart successfully!" in result_output["stdout"]:
            return jsonify({"status": "success", "message": "Cloud Agent added item to cart!"})
        else:
            return jsonify({"status": "failed", "message": result_output["stdout"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
