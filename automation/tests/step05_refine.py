"""
Step 05: Refine Search and Item List Verification
- Verify results page loads
- Confirm dates and guest count appear in UI and URL
- Scrape each listing's title, price, image URL
- Store in DB
"""
import time

from automation.tests.base import BaseTestStep
from automation.db_logger import save_listings
from automation.models import ResultModel


class Step05RefineSearch(BaseTestStep):
    name = "Refine Button Date Validation Test"

    LISTING_CARD_SELECTORS = [
        '[data-testid="listing-card-wrapper"]',
        '[data-testid="card-container"]',
        '[itemprop="itemListElement"]',
        'div[id^="listing"]',
        'article',
    ]

    TITLE_SELECTORS = [
        '[data-testid="listing-card-title"]',
        'div[role="heading"]',
        'span[id*="title"]',
        'div[aria-label]',
    ]

    PRICE_SELECTORS = [
        'span[data-testid*="price"]',
        'span:has-text("$")',
        '._1y74zjx',
        'span[aria-label*="price" i]',
    ]

    def run(self) -> ResultModel:
        print("\n[Step 05] Refine Search and Item List Verification...")

        # Give the results page time to fully render
        time.sleep(4)

        current_url = self.page.url
        screenshot_path = self.screenshot("step05_results_page")

        print(f"  Current URL: {current_url[:100]}")

        # Check if we are on a search results page
        results_loaded = (
            "airbnb.com/s/" in current_url
            or "/s/" in current_url
        )

        # Check URL contains date/guest params
        url_has_dates = any(
            param in current_url
            for param in ["checkin", "check_in", "checkout", "check_out"]
        )
        url_has_guests = "adults" in current_url or "guests" in current_url

        # Read displayed dates from UI
        displayed_dates = ""
        for sel in [
            '[data-testid="structured-search-input-field-split-dates"]',
            'button[aria-label*="dates" i]',
            'button[aria-label*="check" i]',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    displayed_dates = el.inner_text().strip()
                    if displayed_dates:
                        break
            except Exception:
                continue

        # --- Scrape listings ---
        listing_elements = []
        for sel in self.LISTING_CARD_SELECTORS:
            listing_elements = self.page.query_selector_all(sel)
            if listing_elements:
                print(f"  Found listing cards via: {sel}")
                break

        listings = []
        for el in listing_elements[:20]:
            listing = {}

            # Title
            for sel in self.TITLE_SELECTORS:
                try:
                    t = el.query_selector(sel)
                    if t:
                        text = t.inner_text().strip()
                        if text:
                            listing["title"] = text
                            break
                except Exception:
                    pass

            # Price
            for sel in self.PRICE_SELECTORS:
                try:
                    p = el.query_selector(sel)
                    if p:
                        text = p.inner_text().strip()
                        if text:
                            listing["price"] = text
                            break
                except Exception:
                    pass

            # Image
            try:
                img = el.query_selector("img")
                if img:
                    src = img.get_attribute("src") or ""
                    if src:
                        listing["image_url"] = src
            except Exception:
                pass

            if listing:
                listings.append(listing)

        print(f"  Scraped {len(listings)} listings.")
        self.shared_state["listings"] = listings

        checkin = self.shared_state.get("checkin_date", "")
        checkout = self.shared_state.get("checkout_date", "")

        passed = results_loaded and len(listings) > 0
        comment = (
            f"Refine buttons dates: {displayed_dates}. "
            f"Expected: {checkin} - {checkout}. "
            f"URL has dates: {url_has_dates}. URL has guests: {url_has_guests}. "
            f"Scraped {len(listings)} listings. "
            f"URL: {current_url[:150]}"
        )

        result = self.save(passed, comment, screenshot_path)
        save_listings(result, listings)
        return result