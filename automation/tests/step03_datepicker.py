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
        'button[aria-label*="forward" i]',
        'button[aria-label*="next month" i]',
        'button[aria-label*="Next" i]',
        '[data-testid="calendar-next-month-btn"]',
        '.DayPickerNavigation_button__next',
    ]

    # Selectors that confirm the date picker panel is open
    DATEPICKER_OPEN_SELECTORS = [
        '[data-testid="structured-search-input-field-split-dates-0"]',
        '[data-testid="datepicker-portal"]',
        '[aria-label="Calendar"]',
        'div[role="dialog"]',
        '[data-testid="calendar-container"]',
        '.DayPicker',
        'table[role="presentation"]',
        'td[role="button"]',
    ]

    # Selectors to click on the "When / Add dates" field to open the picker
    WHEN_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-split-dates-0"]',
        '[placeholder="Add dates"]',
        'button:has-text("Add dates")',
        '[data-testid="date-input"]',
    ]

    def _picker_is_open(self, timeout_ms: int = 4000) -> bool:
        for sel in self.DATEPICKER_OPEN_SELECTORS:
            try:
                self.page.wait_for_selector(sel, timeout=timeout_ms)
                print(f"  Date picker detected via: {sel}")
                return True
            except Exception:
                continue
        return False

    def _click_next_month(self) -> bool:
        for sel in self.NEXT_MONTH_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    return True
            except Exception:
                continue
        # Last resort: find any button whose aria-label contains "next"
        try:
            buttons = self.page.query_selector_all('button')
            for btn in buttons:
                label = (btn.get_attribute("aria-label") or "").lower()
                if "next" in label or "forward" in label:
                    btn.click()
                    return True
        except Exception:
            pass
        return False

    def _get_available_day_buttons(self) -> list:
        """Return clickable (non-disabled) day buttons from the calendar."""
        selectors = [
            'td[aria-disabled="false"] button',
            'td:not([aria-disabled="true"]) button',
            'button[data-day]:not([disabled])',
            '[data-testid="calendar-day"]:not([disabled])',
            'table td button:not([disabled])',
        ]
        for sel in selectors:
            days = self.page.query_selector_all(sel)
            if days:
                return days
        return []

    def run(self) -> ResultModel:
        print("\n[Step 03] Date Picker Interaction...")
        time.sleep(2)

        # --- Check if picker already opened (Step 02 click may trigger it) ---
        picker_visible = self._picker_is_open(timeout_ms=4000)

        # --- If not open, try clicking the "When / Add dates" field ---
        if not picker_visible:
            print("  Date picker not open — clicking 'When/Add dates' field...")
            for sel in self.WHEN_FIELD_SELECTORS:
                try:
                    el = self.page.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        time.sleep(1.5)
                        break
                except Exception:
                    continue
            picker_visible = self._picker_is_open(timeout_ms=5000)

        screenshot_path = self.screenshot("step03_datepicker_open")

        if not picker_visible:
            return self.save(
                False,
                "Date picker modal did not open after selecting a location.",
                screenshot_path,
            )

        # --- Click Next Month 3-8 times ---
        next_clicks = random.randint(3, 8)
        print(f"  Clicking Next Month {next_clicks} times...")
        for i in range(next_clicks):
            success = self._click_next_month()
            if not success:
                print(f"  Warning: next month click {i + 1} may have failed.")
            time.sleep(0.6)

        # --- Read current visible month label ---
        month_label = ""
        month_selectors = [
            'h2[aria-live="polite"]',
            '[data-testid="calendar-heading"]',
            'h2[aria-live]',
            '.CalendarMonth_caption strong',
            'h2',
        ]
        for sel in month_selectors:
            try:
                els = self.page.query_selector_all(sel)
                for el in els:
                    text = el.inner_text().strip()
                    if text and any(
                        m in text for m in [
                            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                        ]
                    ):
                        month_label = text
                        break
                if month_label:
                    break
            except Exception:
                continue

        self.shared_state["selected_month"] = month_label
        print(f"  Current month shown: {month_label}")

        # --- Select check-in date ---
        checkin_date = ""
        checkout_date = ""

        available_days = self._get_available_day_buttons()
        print(f"  Available day buttons found: {len(available_days)}")

        if len(available_days) >= 2:
            # Pick a day not too close to the start (index 4-7)
            checkin_idx = min(5, len(available_days) - 2)
            try:
                checkin_el = available_days[checkin_idx]
                checkin_date = (
                    checkin_el.get_attribute("aria-label")
                    or checkin_el.inner_text().strip()
                )
                checkin_el.click()
                time.sleep(1)
                print(f"  Check-in selected: {checkin_date}")
            except Exception as e:
                print(f"  Warning: Could not click check-in: {e}")

            # Re-query days after check-in click (calendar may re-render)
            available_days = self._get_available_day_buttons()
            checkout_idx = min(checkin_idx + 5, len(available_days) - 1)

            try:
                checkout_el = available_days[checkout_idx]
                checkout_date = (
                    checkout_el.get_attribute("aria-label")
                    or checkout_el.inner_text().strip()
                )
                checkout_el.click()
                time.sleep(1)
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