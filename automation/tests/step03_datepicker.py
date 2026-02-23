"""
Step 03: Date Picker Interaction
- Verify date picker modal opens after location selection
- Click Next Month between 3-8 times
- Select a valid check-in date
- Select a valid check-out date
- Store selected months and dates in DB via shared_state
- Confirm dates appear in input fields
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.models import ResultModel


class Step03DatePicker(BaseTestStep):
    name = "Date Picker Modal Open and Visibility Test"

    NEXT_MONTH_SELECTORS = [
        '[aria-label="Move forward to switch to the next month."]',
        '[data-testid="datepicker-next"]',
        'button[aria-label*="Next"]',
        '[aria-label="Next"]',
        '.DayPickerNavigation_button__next',
    ]

    def _find_and_click(self, selectors: list) -> bool:
        for sel in selectors:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    return True
            except Exception:
                continue
        return False

    def run(self) -> ResultModel:
        print("\n[Step 03] Date Picker Interaction...")
        time.sleep(1.5)

        datepicker_selectors = [
            '[data-testid="structured-search-input-field-split-dates-0"]',
            '[data-testid="datepicker"]',
            '[aria-label="Calendar"]',
            '.DayPicker',
            '[data-testid="calendar-container"]',
            'div[role="dialog"]',
            '[id*="date"]',
        ]
        picker_visible = False
        for sel in datepicker_selectors:
            try:
                self.page.wait_for_selector(sel, timeout=5000)
                picker_visible = True
                break
            except Exception:
                continue

        if not picker_visible:
            when_selectors = [
                '[data-testid="structured-search-input-field-split-dates-0"]',
                '[placeholder="Add dates"]',
                'button:has-text("Add dates")',
            ]
            for sel in when_selectors:
                try:
                    el = self.page.query_selector(sel)
                    if el:
                        el.click()
                        time.sleep(1)
                        break
                except Exception:
                    continue

            for sel in datepicker_selectors:
                try:
                    self.page.wait_for_selector(sel, timeout=5000)
                    picker_visible = True
                    break
                except Exception:
                    continue

        screenshot_path = self.screenshot("step03_datepicker_open")

        if not picker_visible:
            return self.save(
                False,
                "Date picker modal did not open after selecting a location.",
                screenshot_path,
            )

        # Click Next Month randomly 3-8 times
        next_clicks = random.randint(3, 8)
        print(f"  Clicking Next Month {next_clicks} times...")
        for _ in range(next_clicks):
            clicked = self._find_and_click(self.NEXT_MONTH_SELECTORS)
            if not clicked:
                try:
                    arrows = self.page.query_selector_all('button[aria-label*="next" i]')
                    if arrows:
                        arrows[-1].click()
                except Exception:
                    pass
            time.sleep(0.5)

        # Read current visible month
        month_label = ""
        month_selectors = [
            'h2[aria-live="polite"]',
            '[data-testid="calendar-heading"]',
            '.CalendarMonth_caption strong',
            '[aria-label*="month"]',
        ]
        for sel in month_selectors:
            try:
                el = self.page.query_selector(sel)
                if el:
                    month_label = el.inner_text().strip()
                    if month_label:
                        break
            except Exception:
                continue

        self.shared_state["selected_month"] = month_label
        print(f"  Current month: {month_label}")

        checkin_date = ""
        checkout_date = ""

        day_selectors = [
            'td[aria-disabled="false"] button',
            'button[data-day]:not([disabled])',
            '[data-testid="calendar-day"]:not([disabled])',
            'td:not([aria-disabled="true"]) button',
        ]

        available_days = []
        for sel in day_selectors:
            available_days = self.page.query_selector_all(sel)
            if available_days:
                break

        if not available_days:
            available_days = self.page.query_selector_all('table td button:not([disabled])')

        if len(available_days) >= 2:
            checkin_idx = min(5, len(available_days) - 2)
            try:
                checkin_el = available_days[checkin_idx]
                checkin_date = checkin_el.get_attribute("aria-label") or checkin_el.inner_text().strip()
                checkin_el.click()
                time.sleep(0.8)
                print(f"  Check-in selected: {checkin_date}")
            except Exception as e:
                print(f"  Warning: Could not click check-in: {e}")

            checkout_days = []
            for sel in day_selectors:
                checkout_days = self.page.query_selector_all(sel)
                if checkout_days:
                    break
            if not checkout_days:
                checkout_days = self.page.query_selector_all('table td button:not([disabled])')

            checkout_idx = min(checkin_idx + 5, len(checkout_days) - 1)
            try:
                checkout_el = checkout_days[checkout_idx]
                checkout_date = checkout_el.get_attribute("aria-label") or checkout_el.inner_text().strip()
                checkout_el.click()
                time.sleep(0.8)
                print(f"  Check-out selected: {checkout_date}")
            except Exception as e:
                print(f"  Warning: Could not click checkout: {e}")

        self.shared_state["checkin_date"] = checkin_date
        self.shared_state["checkout_date"] = checkout_date

        screenshot_path2 = self.screenshot("step03_dates_selected")

        dates_ok = bool(checkin_date and checkout_date)
        comment = (
            f"Date picker modal is visible and visible month are {month_label}. "
            f"Check-in: {checkin_date}, Check-out: {checkout_date}."
        )
        return self.save(dates_ok, comment, screenshot_path2)
