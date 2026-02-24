"""
Step 06: Item Details Page Verification

Randomly selects one listing from the search results, clicks its title/link, and:
- Verifies the listing details page opens successfully
- Captures the listing title (h1) and subtitle (h2)
- Collects all image URLs from the FRONT GALLERY only
  (does NOT click 'Show all photos' — only captures the images
   immediately visible in the hero grid on page load)
- Stores all collected details in the database
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.db_logger import save_listing_detail
from automation.models import ResultModel


class Step06ListingDetail(BaseTestStep):
    name = "Item Details Page Verification Test"

    LISTING_CARD_SELECTORS = [
        '[data-testid="listing-card-wrapper"]',
        '[data-testid="card-container"]',
        '[itemprop="itemListElement"]',
        'article',
    ]

    CARD_TITLE_SELECTORS = [
        '[data-testid="listing-card-title"]',
        'div[role="heading"]',
        'span[id*="title"]',
        'h3',
        'h2',
    ]

    def _context_fields(self) -> dict:
        return {
            "selected_location": (self.shared_state.get("selected_location") or ""),
            "selected_month": (self.shared_state.get("selected_month") or ""),
            "checkin_date": (self.shared_state.get("checkin_date") or ""),
            "checkout_date": (self.shared_state.get("checkout_date") or ""),
        }

    def _collect_front_gallery_images(self) -> list:
        """
        Collect only the images visible in the front gallery grid.

        Airbnb shows 5 photos in a hero grid on the listing detail page.
        These are captured individually WITHOUT clicking 'Show all photos'.
        """
        image_urls = []

        # Targeted selectors for the hero/front gallery section only
        gallery_selectors = [
            'div[data-section-id="HERO_DEFAULT"] img',
            'div[data-plugin-in-point-id="HERO_DEFAULT"] img',
            '[data-testid="photo-viewer-section"] img',
            '[data-testid="hero-image-gallery"] img',
            'section[aria-label*="Photo" i] img',
            'div[data-testid="gallery-photo-grid"] img',
        ]

        for sel in gallery_selectors:
            imgs = self.page.query_selector_all(sel)
            if imgs:
                for img in imgs:
                    try:
                        src = img.get_attribute("src") or ""
                        if (src
                                and len(src) > 10
                                and src not in image_urls
                                and ("muscache" in src or "airbnb" in src)):
                            image_urls.append(src)
                    except Exception:
                        continue
                if image_urls:
                    print(f"  Gallery images collected via: {sel}")
                    break

        # Fallback: all Airbnb CDN images visible on the page
        if not image_urls:
            print("  Falling back to all visible Airbnb CDN images...")
            for img in self.page.query_selector_all("img"):
                try:
                    src = img.get_attribute("src") or ""
                    if (src
                            and len(src) > 10
                            and src not in image_urls
                            and ("muscache" in src or "airbnb" in src)):
                        image_urls.append(src)
                except Exception:
                    continue

        return image_urls

    def _collect_listing_candidates(self) -> list:
        candidates = []
        seen_hrefs = set()

        for card_sel in self.LISTING_CARD_SELECTORS:
            cards = self.page.query_selector_all(card_sel)
            if not cards:
                continue

            for card in cards[:30]:
                try:
                    link = card.query_selector('a[href*="/rooms/"]')
                    if not link:
                        continue

                    href = (link.get_attribute("href") or "").strip()
                    if not href or "/rooms/" not in href:
                        continue

                    dedupe_key = href.split("?")[0]
                    if dedupe_key in seen_hrefs:
                        continue

                    title = ""
                    for title_sel in self.CARD_TITLE_SELECTORS:
                        try:
                            t = card.query_selector(title_sel)
                            if t:
                                text = (t.inner_text() or "").strip()
                                if text:
                                    title = text
                                    break
                        except Exception:
                            continue

                    if not title:
                        try:
                            raw = (link.inner_text() or "").strip()
                            title = raw.split("\n")[0].strip() if raw else ""
                        except Exception:
                            title = ""

                    seen_hrefs.add(dedupe_key)
                    candidates.append({"href": href, "title": title})
                except Exception:
                    continue

            if candidates:
                break

        return candidates

    def _click_listing_from_results(self, href: str, title: str) -> bool:
        # First try role-based link click by title.
        if title:
            try:
                loc = self.page.get_by_role("link", name=title).first
                if loc.count() > 0:
                    loc.click(timeout=4000)
                    return True
            except Exception:
                pass

        # Then fallback to exact href/text click in page JS (force same-tab).
        try:
            return bool(self.page.evaluate(
                """
                (payload) => {
                    const { href, title } = payload;
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const wantedHref = (href || '').trim();
                    const wantedTitle = norm(title || '');

                    const links = [...document.querySelectorAll('a[href*="/rooms/"]')]
                        .filter(a => a.offsetParent !== null);

                    let target = null;
                    if (wantedHref) {
                        target = links.find(a => (a.getAttribute('href') || '').trim() === wantedHref);
                    }
                    if (!target && wantedTitle) {
                        target = links.find(a => norm(a.innerText).includes(wantedTitle));
                    }
                    if (!target) return false;

                    target.setAttribute('target', '_self');
                    target.click();
                    return true;
                }
                """,
                {"href": href, "title": title},
            ))
        except Exception:
            return False

    def _wait_for_detail_navigation(self, results_page_url: str, timeout_s: int = 20) -> bool:
        for _ in range(timeout_s):
            current = self.page.url
            if "/rooms/" in current and current != results_page_url:
                return True
            time.sleep(1)
        return False

    def run(self) -> ResultModel:
        print("\n[Step 06] Item Details Page Verification...")
        self.restore_checkpoint()
        self.safe_dismiss_popups()

        results_page_url = self.page.url

        candidates = self._collect_listing_candidates()
        if not candidates:
            screenshot_path = self.screenshot("step06_no_listings")
            return self.save(
                False,
                "No listing titles/links found on results page.",
                screenshot_path,
                **self._context_fields(),
            )

        chosen_idx = random.randint(0, min(len(candidates) - 1, 9))
        chosen = candidates[chosen_idx]
        chosen_href = chosen.get("href", "")
        chosen_title = chosen.get("title", "")

        print(f"  Clicking listing #{chosen_idx + 1}: '{chosen_title or chosen_href}'")

        clicked = self._click_listing_from_results(chosen_href, chosen_title)
        if not clicked:
            screenshot_path = self.screenshot("step06_click_failed")
            return self.save(
                False,
                f"Failed to click selected listing title/link: '{chosen_title or chosen_href}'.",
                screenshot_path,
                **self._context_fields(),
            )

        navigated = self._wait_for_detail_navigation(results_page_url)
        print(f"  Detail navigation success: {navigated}")

        time.sleep(3)
        self.safe_dismiss_popups()
        time.sleep(1)

        current_url = self.page.url
        screenshot_path = self.screenshot("step06_listing_detail")

        detail_loaded = navigated and "/rooms/" in current_url and current_url != results_page_url

        # Capture listing title (h1)
        title = ""
        for sel in [
            'h1[elementtiming="LCP-title"]',
            '[data-section-id="TITLE_DEFAULT"] h1',
            '[data-testid="listing-title"]',
            'h1',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if text:
                        title = text
                        break
            except Exception:
                continue

        # Capture listing subtitle (h2 — location or room type description)
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

        # Collect front gallery images (no 'Show all photos' click)
        image_urls = self._collect_front_gallery_images()

        print(f"  Title   : {title[:80]}")
        print(f"  Subtitle: {subtitle[:80]}")
        print(f"  Images  : {len(image_urls)} (front gallery only, no Show all photos)")
        self.shared_state["selected_listing_title"] = title
        self.shared_state["selected_listing_subtitle"] = subtitle
        self.shared_state["selected_listing_images"] = image_urls
        self.checkpoint("step06_listing_detail_collected")

        passed = detail_loaded and bool(title)
        comment = (
            f"Detail page loaded: {detail_loaded}. "
            f"Clicked listing: '{chosen_title[:100]}'. "
            f"Title: '{title[:100]}'. "
            f"Subtitle: '{subtitle[:100]}'. "
            f"Front gallery images collected: {len(image_urls)}."
        )

        result = self.save(passed, comment, screenshot_path, **self._context_fields())
        save_listing_detail(result, title, subtitle, image_urls)
        return result
