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
        try:
            payload = self.page.evaluate(
                """
                () => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const pickUrl = (img) => {
                        if (!img) return '';
                        return (
                            img.getAttribute('data-original-uri') ||
                            img.getAttribute('src') ||
                            img.currentSrc ||
                            ''
                        ).trim();
                    };
                    const valid = (u) => !!u && u.length > 12 && (u.includes('muscache.com') || u.includes('airbnb'));

                    const ordered = [];
                    const seen = new Set();
                    const add = (u) => {
                        if (!valid(u) || seen.has(u)) return;
                        seen.add(u);
                        ordered.push(u);
                    };

                    // 1) Primary hero image (image 1)
                    const firstCandidates = [
                        document.querySelector('img#FMP-target'),
                        document.querySelector('img[elementtiming="LCP-target"]'),
                        document.querySelector('div[data-section-id="HERO_DEFAULT"] img.i11046vh'),
                        document.querySelector('div[data-plugin-in-point-id="HERO_DEFAULT"] img.i11046vh'),
                    ];
                    for (const img of firstCandidates) {
                        if (!img || !isVisible(img)) continue;
                        add(pickUrl(img));
                        if (ordered.length) break;
                    }

                    // 2..N) Gallery tiles via button aria-label "... image N"
                    const items = [];
                    for (const btn of document.querySelectorAll('button[aria-label*=" image " i], button[aria-label*="image" i]')) {
                        if (!isVisible(btn)) continue;
                        const label = (btn.getAttribute('aria-label') || '').trim();
                        const m = label.match(/\\bimage\\s*(\\d+)\\b/i);
                        if (!m) continue;
                        const idx = Number(m[1] || 0);
                        if (!idx || idx < 2) continue;
                        const img = btn.querySelector('img');
                        const url = pickUrl(img);
                        if (!valid(url)) continue;
                        items.push({ idx, url });
                    }
                    items.sort((a, b) => a.idx - b.idx);
                    for (const item of items) add(item.url);

                    // Secondary fallback within hero if some images missing.
                    if (ordered.length < 5) {
                        const heroImgs = document.querySelectorAll(
                            'div[data-section-id="HERO_DEFAULT"] img, ' +
                            'div[data-plugin-in-point-id="HERO_DEFAULT"] img, ' +
                            'div.cuejewi img, div.inirt6h img, div.ik9m8zb img'
                        );
                        for (const img of heroImgs) {
                            if (!isVisible(img)) continue;
                            add(pickUrl(img));
                        }
                    }
                    return ordered.slice(0, 5);
                }
                """
            )
            if isinstance(payload, list):
                image_urls = [str(u).strip() for u in payload if str(u).strip()]
        except Exception:
            image_urls = []

        if image_urls:
            print("  Gallery images collected via: hero image + aria-label ordered tiles")
            return image_urls

        # Final fallback: any visible Airbnb CDN images.
        print("  Falling back to all visible Airbnb CDN images...")
        for img in self.page.query_selector_all("img"):
            try:
                src = (
                    img.get_attribute("data-original-uri")
                    or img.get_attribute("src")
                    or ""
                )
                if (
                    src
                    and len(src) > 10
                    and src not in image_urls
                    and ("muscache" in src or "airbnb" in src)
                ):
                    image_urls.append(src)
            except Exception:
                continue
        return image_urls[:5]

    def _extract_detail_title_subtitle(self) -> tuple[str, str]:
        title_selectors = [
            'h1.hpipapi[elementtiming="LCP-target"]',
            'h1[elementtiming="LCP-target"]',
            'h1[tabindex="-1"]',
            '[data-section-id="TITLE_DEFAULT"] h1',
            '[data-testid="listing-title"]',
            'h1',
        ]
        subtitle_selectors = [
            'h2.hpipapi[elementtiming="LCP-target"]',
            'h2[elementtiming="LCP-target"]',
            'h2[tabindex="-1"]',
            '[data-testid="listing-subtitle"]',
            '[data-section-id="OVERVIEW_DEFAULT"] h2',
            'h2',
        ]

        title = ""
        subtitle = ""
        for _ in range(10):
            if not title:
                for sel in title_selectors:
                    try:
                        el = self.page.query_selector(sel)
                        if not el:
                            continue
                        text = (el.inner_text() or "").strip()
                        if text:
                            title = text
                            break
                    except Exception:
                        continue

            if not subtitle:
                for sel in subtitle_selectors:
                    try:
                        els = self.page.query_selector_all(sel)
                        for el in els:
                            text = (el.inner_text() or "").strip()
                            if text and text != title:
                                subtitle = text
                                break
                        if subtitle:
                            break
                    except Exception:
                        continue

            if title:
                break
            time.sleep(0.4)

        return title, subtitle

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

    def _wait_for_detail_content_ready(self, timeout_s: int = 20) -> bool:
        """
        Wait until detail header or hero gallery content is rendered.
        This avoids extracting title/subtitle/images before Airbnb finishes hydration.
        """
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        for _ in range(timeout_s * 2):
            try:
                if "/rooms/" not in self.page.url:
                    time.sleep(0.5)
                    continue
                h1 = self.page.query_selector(
                    'h1.hpipapi[elementtiming="LCP-target"], h1[elementtiming="LCP-target"], h1[tabindex="-1"], h1'
                )
                hero = self.page.query_selector(
                    'img#FMP-target, img[elementtiming="LCP-target"], div[data-section-id="HERO_DEFAULT"] img'
                )
                if h1 or hero:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def run(self) -> ResultModel:
        print("\n[Step 06] Item Details Page Verification...")
        self.restore_checkpoint()
        self.safe_dismiss_popups()

        results_page_url = self.page.url

        candidates = self._collect_listing_candidates()
        if not candidates:
            return self.save(
                False,
                "No listing titles/links found on results page.",
                "",
                **self._context_fields(),
            )

        chosen_idx = random.randint(0, min(len(candidates) - 1, 9))
        chosen = candidates[chosen_idx]
        chosen_href = chosen.get("href", "")
        chosen_title = chosen.get("title", "")

        print(f"  Clicking listing #{chosen_idx + 1}: '{chosen_title or chosen_href}'")

        clicked = self._click_listing_from_results(chosen_href, chosen_title)
        if not clicked:
            return self.save(
                False,
                f"Failed to click selected listing title/link: '{chosen_title or chosen_href}'.",
                "",
                **self._context_fields(),
            )

        navigated = self._wait_for_detail_navigation(results_page_url)
        print(f"  Detail navigation success: {navigated}")

        content_ready = self._wait_for_detail_content_ready(timeout_s=20)
        print(f"  Detail content ready: {content_ready}")
        self.safe_dismiss_popups()
        time.sleep(0.8)

        current_url = self.page.url

        detail_loaded = navigated and "/rooms/" in current_url and current_url != results_page_url

        # Capture listing title/subtitle from detail header.
        title, subtitle = self._extract_detail_title_subtitle()

        # Collect front gallery images (no 'Show all photos' click)
        image_urls = self._collect_front_gallery_images()

        # Take screenshot only after collecting detail fields.
        screenshot_path = self.screenshot("step06_listing_detail")

        print(f"  Title   : {title[:80]}")
        print(f"  Subtitle: {subtitle[:80]}")
        print(f"  Images  : {len(image_urls)} (front gallery only, no Show all photos)")
        self.shared_state["selected_listing_title"] = title
        self.shared_state["selected_listing_subtitle"] = subtitle
        self.shared_state["selected_listing_images"] = image_urls
        self.checkpoint("step06_listing_detail_collected")

        passed = detail_loaded and bool(title) and content_ready
        comment = (
            f"Detail page loaded: {detail_loaded}. "
            f"Content ready: {content_ready}. "
            f"Clicked listing: '{chosen_title[:100]}'. "
            f"Title: '{title[:100]}'. "
            f"Subtitle: '{subtitle[:100]}'. "
            f"Front gallery images collected: {len(image_urls)}."
        )

        result = self.save(passed, comment, screenshot_path, **self._context_fields())
        save_listing_detail(result, title, subtitle, image_urls)
        return result
