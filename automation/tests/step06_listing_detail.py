"""
Step 06: Item Details Page Verification
- Randomly select one listing from results
- Click on it
- Verify details page loads
- Capture title, subtitle, and all image URLs
- Store in DB
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.db_logger import save_listing_detail
from automation.models import ResultModel


class Step06ListingDetail(BaseTestStep):
    name = "Item Details Page Verification Test"

    LISTING_LINK_SELECTORS = [
        '[data-testid="listing-card-wrapper"] a[href*="/rooms/"]',
        'a[href*="airbnb.com/rooms/"]',
        '[itemprop="itemListElement"] a',
        '[data-testid="card-container"] a',
        'article a[href*="/rooms/"]',
        'a[href*="/rooms/"]',
    ]

    def run(self) -> ResultModel:
        print("\n[Step 06] Item Details Page Verification...")

        listings_page_url = self.page.url

        # --- Collect listing hrefs directly ---
        listing_hrefs = []
        for sel in self.LISTING_LINK_SELECTORS:
            try:
                links = self.page.query_selector_all(sel)
                for link in links:
                    href = link.get_attribute("href") or ""
                    if href and href not in listing_hrefs:
                        listing_hrefs.append(href)
                if listing_hrefs:
                    print(f"  Found {len(listing_hrefs)} listing links via: {sel}")
                    break
            except Exception:
                continue

        # Fallback: grab all <a> with /rooms/ in href
        if not listing_hrefs:
            try:
                all_links = self.page.query_selector_all("a[href]")
                for link in all_links:
                    href = link.get_attribute("href") or ""
                    if "/rooms/" in href and href not in listing_hrefs:
                        listing_hrefs.append(href)
                print(f"  Fallback found {len(listing_hrefs)} /rooms/ links.")
            except Exception:
                pass

        if not listing_hrefs:
            screenshot_path = self.screenshot("step06_no_listings")
            return self.save(False, "No listing links found to click.", screenshot_path)

        # --- Choose a random listing (from first 10) ---
        chosen_idx = random.randint(0, min(len(listing_hrefs) - 1, 9))
        href = listing_hrefs[chosen_idx]

        # Ensure absolute URL
        if href.startswith("/"):
            href = f"https://www.airbnb.com{href}"
        elif not href.startswith("http"):
            href = f"https://www.airbnb.com/{href}"

        print(f"  Navigating to listing: {href[:80]}")

        try:
            self.page.goto(href, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"  goto() failed: {e} — trying click approach.")
            try:
                self.page.go_back()
                time.sleep(2)
                links = self.page.query_selector_all("a[href]")
                for link in links:
                    h = link.get_attribute("href") or ""
                    if "/rooms/" in h:
                        link.click()
                        break
            except Exception:
                pass

        time.sleep(3)
        self.dismiss_popups()
        time.sleep(1)

        current_url = self.page.url
        screenshot_path = self.screenshot("step06_listing_detail")

        detail_loaded = (
            "airbnb.com/rooms" in current_url
            or ("/rooms/" in current_url)
            or (current_url != listings_page_url and "airbnb.com" in current_url)
        )

        # --- Capture title ---
        title = ""
        for sel in [
            'h1[elementtiming="LCP-title"]',
            'h1',
            '[data-testid="listing-title"]',
            '[data-section-id="TITLE_DEFAULT"] h1',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    title = el.inner_text().strip()
                    if title:
                        break
            except Exception:
                continue

        # --- Capture subtitle ---
        subtitle = ""
        for sel in [
            '[data-section-id="OVERVIEW_DEFAULT"] h2',
            '[data-testid="listing-subtitle"]',
            'h2',
        ]:
            try:
                els = self.page.query_selector_all(sel)
                for el in els:
                    text = el.inner_text().strip()
                    if text and text != title:
                        subtitle = text
                        break
                if subtitle:
                    break
            except Exception:
                continue

        # --- Collect image URLs ---
        image_urls = []
        for img in self.page.query_selector_all("img"):
            try:
                src = img.get_attribute("src") or ""
                if (
                    src
                    and src not in image_urls
                    and len(src) > 10
                    and ("muscache" in src or "airbnb" in src)
                ):
                    image_urls.append(src)
            except Exception:
                continue

        print(f"  Title: {title[:80]}")
        print(f"  Subtitle: {subtitle[:80]}")
        print(f"  Images found: {len(image_urls)}")

        passed = detail_loaded and bool(title)
        comment = (
            f"Listing detail page loaded: {detail_loaded}. "
            f"Title: '{title[:100]}'. Subtitle: '{subtitle[:100]}'. "
            f"Images collected: {len(image_urls)}."
        )

        result = self.save(passed, comment, screenshot_path)
        save_listing_detail(result, title, subtitle, image_urls)
        return result