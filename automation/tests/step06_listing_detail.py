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

    def run(self) -> ResultModel:
        print("\n[Step 06] Item Details Page Verification...")

        listings_page_url = self.page.url

        listing_selectors = [
            '[data-testid="listing-card-wrapper"] a',
            '[itemprop="itemListElement"] a',
            'article a',
        ]
        listing_links = []
        for sel in listing_selectors:
            listing_links = self.page.query_selector_all(sel)
            if listing_links:
                break

        if not listing_links:
            screenshot_path = self.screenshot("step06_no_listings")
            return self.save(False, "No listing links found to click.", screenshot_path)

        chosen_idx = random.randint(0, min(len(listing_links) - 1, 9))
        try:
            href = listing_links[chosen_idx].get_attribute("href") or ""
            if href:
                if href.startswith("/"):
                    href = f"https://www.airbnb.com{href}"
                self.page.goto(href, wait_until="domcontentloaded", timeout=30000)
            else:
                listing_links[chosen_idx].click()
        except Exception as e:
            print(f"  Warning clicking listing: {e}")
            try:
                listing_links[0].click()
            except Exception:
                pass

        time.sleep(3)
        self.dismiss_popups()
        time.sleep(1)

        current_url = self.page.url
        screenshot_path = self.screenshot("step06_listing_detail")

        detail_loaded = (
            "airbnb.com/rooms" in current_url
            or ("airbnb.com" in current_url and current_url != listings_page_url)
        )

        title = ""
        for sel in [
            'h1',
            '[data-testid="listing-title"]',
            '[data-section-id="TITLE_DEFAULT"] h1',
            'h1[elementtiming="LCP-title"]',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    title = el.inner_text().strip()
                    if title:
                        break
            except Exception:
                continue

        subtitle = ""
        for sel in [
            '[data-testid="listing-subtitle"]',
            '[data-section-id="OVERVIEW_DEFAULT"] h2',
            'h2',
            'section[aria-label*="location"] span',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    subtitle = el.inner_text().strip()
                    if subtitle and subtitle != title:
                        break
            except Exception:
                continue

        image_urls = []
        for img in self.page.query_selector_all(
            'img[src*="a0.muscache.com"], img[src*="airbnb.com"], section img'
        ):
            try:
                src = img.get_attribute("src") or ""
                if src and src not in image_urls and len(src) > 10:
                    image_urls.append(src)
            except Exception:
                continue

        for div in self.page.query_selector_all('[style*="background-image"]'):
            try:
                style = div.get_attribute("style") or ""
                if "url(" in style:
                    url = style.split("url(")[1].split(")")[0].strip('"\'')
                    if url not in image_urls:
                        image_urls.append(url)
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
