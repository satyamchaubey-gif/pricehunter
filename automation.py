import asyncio
import os
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PriceHunterBot")

class ShoppingBot:
    """
    Autonomous agent to handle the 'Add to Cart' and 'Checkout' flow.
    """
    def __init__(self, headless=False, session_path="/root/.browser_session"):
        self.headless = headless
        self.session_path = session_path

    async def save_session(self, url: str):
        """
        Opens a browser for the user to log in manually, then saves the session.
        """
        async with async_playwright() as p:
            # Must be headed mode for the user to log in
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            logger.info(f"Opening {url} for manual login. Please log in and then close the browser window.")
            await page.goto(url)

            # Wait for the user to close the browser window
            while True:
                if len(context.pages) == 0:
                    break
                await asyncio.sleep(1)

            # Save the storage state (cookies, local storage) to a file
            await context.storage_state(path=self.session_path)
            logger.info(f"Session saved to {self.session_path}")
            await browser.close()
            return {"status": "success", "message": "Session saved successfully!"}

    async def add_to_cart(self, url: str, use_session: bool = False):
        """
        Navigates to a product URL and attempts to add it to the cart.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            if use_session and os.path.exists(self.session_path):
                context = await browser.new_context(storage_state=self.session_path)
                logger.info("Using saved session for authentication.")
            else:
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )

            page = await context.new_page()

            try:
                logger.info(f"Navigating to: {url}")
                # Use a longer timeout and wait for network idle to ensure the page is fully loaded
                await page.goto(url, wait_until="networkidle", timeout=90000)

                # 1. Handle pop-ups and overlays
                popup_selectors = [
                    "button[aria-label='Close']", ".close-modal", ".modal-close",
                    "text=Close", "text=No thanks", "[id*='close']", "[class*='close']"
                ]
                for selector in popup_selectors:
                    try:
                        if await page.is_visible(selector):
                            await page.click(selector, timeout=2000)
                    except:
                        pass

                # 2. Smart Search for 'Add to Cart' buttons
                # We try multiple strategies: Text, ID, and Class
                cart_keywords = ["add to cart", "add to basket", "buy now", "cart me", "purchase"]

                # Strategy A: Look for buttons with keywords
                buttons = await page.query_selector_all("button, a, input[type='button'], input[type='submit']")
                for btn in buttons:
                    text = await btn.inner_text()
                    if text and any(kw in text.lower() for kw in cart_keywords):
                        logger.info("Found button by text. Clicking...")
                        await btn.click()
                        await asyncio.sleep(5)
                        return {"status": "success", "message": "Item added to cart successfully!"}

                # Strategy B: Look for common ID/Class patterns
                common_selectors = [
                    "[id*='add-to-cart']", "[id*='buy-now']", "[class*='add-to-cart']",
                    "[class*='buy-now']", "[data-automation='addToCart']", "[id='add-to-cart-button']"
                ]
                for selector in common_selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if btn:
                            logger.info(f"Found button by selector {selector}. Clicking...")
                            await btn.click()
                            await asyncio.sleep(5)
                            return {"status": "success", "message": "Item added to cart successfully!"}
                    except:
                        pass

                # Strategy C: Last resort - find any button that looks like a primary action
                # Look for a button that is prominent and has a 'cart' or 'buy' related class
                try:
                    btn = await page.locator("button:has-text('Add')").first.click(timeout=5000)
                    await asyncio.sleep(5)
                    return {"status": "success", "message": "Item added to cart successfully!"}
                except:
                    pass

                logger.error("Could not find a valid 'Add to Cart' button after all strategies.")
                return {"status": "failed", "message": "Could not find the Add to Cart button. The site might be blocking the bot or using a non-standard layout."}

            except Exception as e:
                logger.error(f"Automation error: {e}")
                return {"status": "error", "message": str(e)}
            finally:
                await browser.close()

# For direct testing:
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
        bot = ShoppingBot(headless=True) # Headless in cloud sandbox
        result = asyncio.run(bot.add_to_cart(url))
        # IMPORTANT: Print the result so the Flask server can read it from stdout
        print(result["message"])
    else:
        print("Usage: python automation.py <url>")
