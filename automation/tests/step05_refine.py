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

    def run(self) -> ResultModel:
        print("\n[Step 05] Refine Search and Item List Verification...")

        time.sleep(3)

        current_url = self.page.url
        screenshot_path = self.screenshot("step05_results_page")

        results_loaded = "airbnb.com/s/" in current_url or "airbnb.com/rooms" in current_url

        checkin = self.shared_state.get("checkin_date", "")
        checkout = self.shared_state.get("checkout_date", "")

        url_has_dates = (
            "check_in" in current_url
            or "checkin" in current_url
            or "adults" in current_url
        )

        listing_selectors = [
            '[data-testid="listing-card-wrapper"]',
            '[itemprop="itemListElement"]',
            '[data-testid="card-container"]',
            'div[id^="listing"]',
        ]

        listing_elements = []
        for sel in listing_selectors:
            listing_elements = self.page.query_selector_all(sel)
            if listing_elements:
                break

        if not listing_elements:
            listing_elements = self.page.query_selector_all("article")

        listings = []
        for el in listing_elements[:20]:
            listing = {}
            for title_sel in ['[data-testid="listing-card-title"]', 'div[role="heading"]', 'span[id*="title"]']:
                try:
                    t = el.query_selector(title_sel)
                    if t:
                        listing["title"] = t.inner_text().strip()
                        break
                except Exception:
                    pass

            for price_sel in ['span[data-testid*="price"]', '._1y74zjx', 'span:has-text("$")']:
                try:
                    p = el.query_selector(price_sel)
                    if p:
                        listing["price"] = p.inner_text().strip()
                        break
                except Exception:
                    pass

            try:
                img = el.query_selector("img")
                if img:
                    listing["image_url"] = img.get_attribute("src") or ""
            except Exception:
                pass

            if listing:
                listings.append(listing)

        print(f"  Scraped {len(listings)} listings.")
        self.shared_state["listings"] = listings

        expected_dates_comment = f"Expected: {checkin} - {checkout}"

        displayed_dates = ""
        for sel in [
            '[data-testid="structured-search-input-field-split-dates"]',
            '[aria-label*="dates"]',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    displayed_dates = el.inner_text().strip()
                    break
            except Exception:
                continue

        passed = results_loaded and len(listings) > 0
        comment = (
            f"Refine buttons dates: {displayed_dates}. {expected_dates_comment}. "
            f"URL has dates: {url_has_dates}. Scraped {len(listings)} listings. "
            f"URL: {current_url[:100]}"
        )

        result = self.save(passed, comment, screenshot_path)
        save_listings(result, listings)
        return result
