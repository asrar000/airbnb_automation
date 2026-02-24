"""
Step 05: Refine Search and Item List Verification

After Step 04 clicks Search, the browser navigates to the results page.
This step:
- Waits for the /s/ results URL to confirm navigation succeeded
- Confirms selected dates and guest count appear in the page UI
- Validates selected dates and guest count are present in the page URL
- Scrapes each listing's title, price, and image URL (up to 20)
- Stores collected listing data in the database
"""
import re
import time
from urllib.parse import parse_qs, urlparse

from automation.tests.base import BaseTestStep
from automation.db_logger import save_listings, run_in_thread
from automation.models import ResultModel


class Step05RefineSearch(BaseTestStep):
    name = "Refine Button Date Validation Test"
    STEP04_RESULT_NAME = "Guest Picker Interaction Test"
    STEP03_RESULT_NAME = "Date Picker Modal Open and Visibility Test"

    LISTING_CARD_SELECTORS = [
        '[data-testid="listing-card-wrapper"]',
        '[data-testid="card-container"]',
        '[itemprop="itemListElement"]',
        'article',
    ]

    def _wait_for_results_page(self) -> bool:
        """Poll until URL contains /s/ indicating the search results page."""
        for _ in range(15):
            if "/s/" in self.page.url:
                return True
            time.sleep(1)
        return False

    @staticmethod
    def _extract_first_int(text: str):
        match = re.search(r"\d+", text or "")
        if not match:
            return None
        try:
            return int(match.group(0))
        except Exception:
            return None

    @staticmethod
    def _extract_day_token(date_text: str) -> str:
        # Supports labels like:
        # - "May 7, 2026"
        # - "Friday, May 07, 2026"
        # - "Jul 8"
        text = date_text or ""
        month_pattern = (
            r"january|february|march|april|may|june|july|august|"
            r"september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
        )
        month_first = re.search(
            rf"\b(?:{month_pattern})\.?\s+([0-3]?\d)\b",
            text,
            re.IGNORECASE,
        )
        if month_first:
            return month_first.group(1).lstrip("0") or "0"

        day_first = re.search(
            rf"\b([0-3]?\d)(?:st|nd|rd|th)?\s+(?:of\s+)?(?:{month_pattern})\b",
            text,
            re.IGNORECASE,
        )
        if day_first:
            return day_first.group(1).lstrip("0") or "0"

        fallback = re.search(r"\b([0-3]?\d)\b", text)
        if fallback:
            return fallback.group(1).lstrip("0") or "0"
        return ""

    @staticmethod
    def _extract_day_from_iso(date_text: str) -> str:
        match = re.search(r"\b\d{4}-\d{2}-(\d{2})\b", date_text or "")
        if not match:
            return ""
        return match.group(1).lstrip("0") or "0"

    def _ui_contains_selected_days(self, checkin: str, checkout: str, displayed_dates: str) -> bool:
        if not (checkin and checkout and displayed_dates):
            return False
        checkin_day = self._extract_day_token(checkin)
        checkout_day = self._extract_day_token(checkout)
        if not (checkin_day and checkout_day):
            return False
        normalized = displayed_dates.lower()
        has_checkin = bool(re.search(rf"\b0?{re.escape(checkin_day)}\b", normalized))
        has_checkout = bool(re.search(rf"\b0?{re.escape(checkout_day)}\b", normalized))
        return has_checkin and has_checkout

    def _restore_context_from_db(self) -> bool:
        fields = [
            "selected_location",
            "selected_month",
            "checkin_date",
            "checkout_date",
            "comment",
        ]

        def _fetch(test_name: str):
            return (
                ResultModel.objects.filter(test_case=test_name, passed=True)
                .order_by("-created_at")
                .values(*fields)
                .first()
            )

        payload_step04 = None
        payload_step03 = None
        try:
            payload_step04 = run_in_thread(lambda: _fetch(self.STEP04_RESULT_NAME))
        except Exception:
            payload_step04 = None
        try:
            payload_step03 = run_in_thread(lambda: _fetch(self.STEP03_RESULT_NAME))
        except Exception:
            payload_step03 = None

        restored = False
        payloads = [payload_step04, payload_step03]
        for payload in payloads:
            if not payload:
                continue
            if payload.get("selected_location") and not self.shared_state.get("selected_location"):
                self.shared_state["selected_location"] = payload.get("selected_location")
                restored = True
            if payload.get("selected_month") and not self.shared_state.get("selected_month"):
                self.shared_state["selected_month"] = payload.get("selected_month")
                restored = True
            if payload.get("checkin_date") and not self.shared_state.get("checkin_date"):
                self.shared_state["checkin_date"] = payload.get("checkin_date")
                restored = True
            if payload.get("checkout_date") and not self.shared_state.get("checkout_date"):
                self.shared_state["checkout_date"] = payload.get("checkout_date")
                restored = True

        # Guest count is not a DB field, but Step 04 comment includes it.
        if not self.shared_state.get("guest_count") and payload_step04:
            comment = payload_step04.get("comment") or ""
            guest_count_match = re.search(r"Search guest count:\s*(\d+)", comment, re.IGNORECASE)
            if guest_count_match:
                self.shared_state["guest_count"] = int(guest_count_match.group(1))
                restored = True
            breakdown_match = re.search(
                r"adults=(\d+),\s*children=(\d+),\s*infants=(\d+),\s*pets=(\d+)",
                comment,
                re.IGNORECASE,
            )
            if breakdown_match and not self.shared_state.get("guest_breakdown"):
                self.shared_state["guest_breakdown"] = {
                    "adults": int(breakdown_match.group(1)),
                    "children": int(breakdown_match.group(2)),
                    "infants": int(breakdown_match.group(3)),
                    "pets": int(breakdown_match.group(4)),
                }
                restored = True

        return restored

    def _ensure_context(self) -> None:
        if not self.shared_state.get("selected_location"):
            self.shared_state["selected_location"] = (
                self.shared_state.get("chosen_suggestion")
                or self.shared_state.get("selected_country")
                or ""
            )

        missing_dates = not (
            (self.shared_state.get("checkin_date") or "").strip()
            and (self.shared_state.get("checkout_date") or "").strip()
        )
        missing_location = not (self.shared_state.get("selected_location") or "").strip()
        missing_guest = int(self.shared_state.get("guest_count") or 0) <= 0
        if missing_dates or missing_location or missing_guest:
            restored = self._restore_context_from_db()
            if restored:
                print("  Restored context for Step 05 from DB backup.")
                self.checkpoint("step05_context_restored_from_db")

    def run(self) -> ResultModel:
        print("\n[Step 05] Refine Search and Item List Verification...")
        self.restore_checkpoint()
        self._ensure_context()
        self.safe_dismiss_popups()

        # Wait for navigation to search results page
        on_results = self._wait_for_results_page()
        time.sleep(3)

        current_url = self.page.url
        print(f"  Current URL: {current_url[:120]}")

        screenshot_path = self.screenshot("step05_results_page")

        results_loaded = "/s/" in current_url
        parsed_url = urlparse(current_url)
        query = parse_qs(parsed_url.query)

        # Validate selected filters appear in URL query params
        checkin_param = (query.get("checkin") or query.get("check_in") or [""])[0]
        checkout_param = (query.get("checkout") or query.get("check_out") or [""])[0]
        adults_param = (query.get("adults") or ["0"])[0]
        children_param = (query.get("children") or ["0"])[0]
        infants_param = (query.get("infants") or ["0"])[0]
        pets_param = (query.get("pets") or ["0"])[0]
        guests_param = (query.get("guests") or ["0"])[0]

        url_has_checkin = bool(checkin_param)
        url_has_checkout = bool(checkout_param)
        adults_count = self._extract_first_int(adults_param) or 0
        children_count = self._extract_first_int(children_param) or 0
        infants_count = self._extract_first_int(infants_param) or 0
        pets_count = self._extract_first_int(pets_param) or 0
        guests_count = self._extract_first_int(guests_param) or 0

        url_guest_total = adults_count + children_count + infants_count + pets_count
        if url_guest_total == 0 and guests_count > 0:
            url_guest_total = guests_count
        url_has_guests = url_guest_total > 0

        # Read displayed dates from the UI filter/refine bar
        displayed_dates = ""
        for sel in [
            '[data-testid="structured-search-input-field-split-dates"]',
            'button[aria-label*="check" i]',
            'button[aria-label*="dates" i]',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if text:
                        displayed_dates = text
                        break
            except Exception:
                pass

        # Read displayed guest count from UI
        displayed_guests = ""
        for sel in [
            '[data-testid="structured-search-input-field-guests-button"]',
            'button[aria-label*="guest" i]',
        ]:
            try:
                el = self.page.query_selector(sel)
                if el:
                    text = el.inner_text().strip()
                    if text:
                        displayed_guests = text
                        break
            except Exception:
                pass

        # Scrape listing cards
        listing_elements = []
        for sel in self.LISTING_CARD_SELECTORS:
            listing_elements = self.page.query_selector_all(sel)
            if listing_elements:
                print(f"  Listing cards found via: {sel}")
                break

        listings = []
        for el in listing_elements[:20]:
            listing = {}

            # Title
            for title_sel in [
                '[data-testid="listing-card-title"]',
                'div[role="heading"]',
                'span[id*="title"]',
            ]:
                try:
                    t = el.query_selector(title_sel)
                    if t:
                        text = t.inner_text().strip()
                        if text:
                            listing["title"] = text
                            break
                except Exception:
                    pass

            # Price
            for price_sel in [
                'span[data-testid*="price"]',
                'span:has-text("$")',
                '._1y74zjx',
            ]:
                try:
                    p = el.query_selector(price_sel)
                    if p:
                        text = p.inner_text().strip()
                        if text:
                            listing["price"] = text
                            break
                except Exception:
                    pass

            # Image URL
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
        self.checkpoint("step05_results_scraped")

        checkin = self.shared_state.get("checkin_date", "")
        checkout = self.shared_state.get("checkout_date", "")
        guests = self.shared_state.get("guest_count", 0)
        guest_breakdown = self.shared_state.get("guest_breakdown", {}) or {}

        ui_has_dates = self._ui_contains_selected_days(checkin, checkout, displayed_dates)
        ui_guest_count = self._extract_first_int(displayed_guests) or 0
        ui_has_guests = bool(displayed_guests) and ui_guest_count > 0

        selected_checkin_day = self._extract_day_token(checkin)
        selected_checkout_day = self._extract_day_token(checkout)
        url_checkin_day = self._extract_day_from_iso(checkin_param)
        url_checkout_day = self._extract_day_from_iso(checkout_param)
        url_dates_match_selected = bool(
            selected_checkin_day
            and selected_checkout_day
            and url_checkin_day
            and url_checkout_day
            and selected_checkin_day == url_checkin_day
            and selected_checkout_day == url_checkout_day
        )

        selected_guest_total = self._extract_first_int(str(guests)) or 0
        if selected_guest_total <= 0 and url_guest_total > 0:
            # If refresh cleared checkpoint guest count, use URL-applied guests.
            selected_guest_total = url_guest_total
            self.shared_state["guest_count"] = url_guest_total

        expected_ui_guest_total = selected_guest_total
        expected_url_guest_total = selected_guest_total

        if guest_breakdown:
            expected_ui_guest_total = int(guest_breakdown.get("adults", 0)) + int(guest_breakdown.get("children", 0))
            expected_url_guest_total = (
                int(guest_breakdown.get("adults", 0))
                + int(guest_breakdown.get("children", 0))
                + int(guest_breakdown.get("infants", 0))
                + int(guest_breakdown.get("pets", 0))
            )

        ui_guests_match_selected = expected_ui_guest_total > 0 and ui_guest_count == expected_ui_guest_total
        url_guests_match_selected = expected_url_guest_total > 0 and (
            url_guest_total == expected_url_guest_total or url_guest_total == expected_ui_guest_total
        )

        passed = all(
            [
                on_results,
                results_loaded,
                url_has_checkin,
                url_has_checkout,
                url_dates_match_selected,
                url_has_guests,
                url_guests_match_selected,
                ui_has_dates,
                ui_has_guests,
                ui_guests_match_selected,
                len(listings) > 0,
            ]
        )
        comment = (
            f"Results page loaded: {results_loaded}. "
            f"Dates in UI: '{displayed_dates}'. Expected: {checkin} - {checkout}. "
            f"Guests in UI: '{displayed_guests}'. Selected: {guests}. "
            f"URL has checkin: {url_has_checkin}, checkout: {url_has_checkout}, "
            f"dates match selected: {url_dates_match_selected}. "
            f"guests: {url_has_guests} (total in URL: {url_guest_total}, "
            f"expected total: {expected_url_guest_total}, "
            f"matches selected: {url_guests_match_selected}). "
            f"UI dates match selected: {ui_has_dates}. "
            f"UI guests present: {ui_has_guests} (count: {ui_guest_count}, "
            f"expected: {expected_ui_guest_total}, "
            f"matches selected: {ui_guests_match_selected}). "
            f"Listings scraped: {len(listings)}."
        )

        result = self.save(
            passed,
            comment,
            screenshot_path,
            selected_location=(self.shared_state.get("selected_location") or ""),
            selected_month=(self.shared_state.get("selected_month") or ""),
            checkin_date=(self.shared_state.get("checkin_date") or ""),
            checkout_date=(self.shared_state.get("checkout_date") or ""),
        )
        save_listings(result, listings)
        return result
