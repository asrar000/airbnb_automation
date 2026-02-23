"""
Step 01: Website Landing and Initial Search Setup
- Open Airbnb homepage
- Clear cookies/cache/storage
- Dismiss popups
- Verify homepage loads
- Select random country from top-20 list
- Type country into search field
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.models import ResultModel

TOP_20_COUNTRIES = [
    "United States",
    "China",
    "India",
    "Brazil",
    "Russia",
    "Mexico",
    "Japan",
    "Germany",
    "France",
    "United Kingdom",
    "Italy",
    "South Korea",
    "Canada",
    "Australia",
    "Spain",
    "Indonesia",
    "Turkey",
    "Saudi Arabia",
    "Argentina",
    "South Africa",
]


class Step01LandingAndSearch(BaseTestStep):
    name = "Website Landing and Initial Search Setup"

    def run(self) -> ResultModel:
        print("\n[Step 01] Landing and Initial Search Setup...")

        # --- Clear storage ---
        self.page.context.clear_cookies()
        self.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")

        # --- Navigate ---
        self.page.goto(
            self.shared_state.get("target_url", "https://www.airbnb.com/"),
            wait_until="networkidle",
            timeout=60000,
        )
        self.wait(2)

        # --- Dismiss popups ---
        self.dismiss_popups()
        self.wait(1)

        # --- Verify homepage loaded ---
        title = self.page.title()
        homepage_ok = (
            "airbnb" in title.lower()
            or self.page.query_selector('[data-testid="structured-search-input-field-query"]') is not None
        )

        screenshot_path = self.screenshot("step01_homepage")

        if not homepage_ok:
            return self.save(False, f"Homepage did not load correctly. Title: {title}", screenshot_path)

        # --- Select a random country ---
        country = random.choice(TOP_20_COUNTRIES)
        self.shared_state["selected_country"] = country
        print(f"  Selected country: {country}")

        # --- Click search field ---
        search_selectors = [
            '[data-testid="structured-search-input-field-query"]',
            '[placeholder="Search destinations"]',
            'input[name="query"]',
            '[data-testid="search-tabbed-destination-input"]',
        ]
        clicked = False
        for sel in search_selectors:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            try:
                self.page.click('[data-testid="structured-search-input-field-query"]', timeout=5000)
                clicked = True
            except Exception:
                pass

        self.wait(1)

        # --- Type country human-like ---
        for char in country:
            self.page.keyboard.type(char)
            time.sleep(random.uniform(0.05, 0.15))

        self.wait(1.5)
        screenshot_path2 = self.screenshot("step01_typed_country")

        comment = (
            f"Homepage loaded successfully. Title: '{title}'. "
            f"Selected country: '{country}' and typed into search field."
        )
        return self.save(True, comment, screenshot_path2)
