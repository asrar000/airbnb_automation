"""
Step 03: Date Picker Modal Open and Visibility Test

After clicking a suggestion in Step 01, Airbnb automatically opens
the date picker. This step:
- Verifies the date picker calendar is visible
- Clicks Next Month randomly 3-8 times
- Selects a valid check-in date
- Selects a valid check-out date (after check-in)
- Confirms the selected dates appear in the date input fields
- Stores month + dates in shared_state for Step 04/05 validation
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.models import ResultModel


class Step03DatePicker(BaseTestStep):
    name = "Date Picker Modal Open and Visibility Test"

    NEXT_MONTH_SELECTORS = [
        '[aria-label*="Move forward" i]',
        '[aria-label="Move forward to switch to the next month."]',
        'button[aria-label*="forward" i]',
        'button[aria-label*="next month" i]',
        'button[aria-label*="Next" i]',
        'button[data-testid*="calendar-next"]',
    ]

    DATEPICKER_SELECTORS = [
        '[data-testid="datepicker-portal"]',
        'div[role="dialog"] [data-testid*="calendar"]',
        'div[role="dialog"] table',
        '[data-testid="structured-search-input-field-dates-panel"]',
    ]

    WHEN_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-split-dates-0"]',
        '[data-testid="structured-search-input-field-split-dates-1"]',
        '[data-testid="structured-search-input-field-dates-button"]',
        'button[aria-label*="check in" i]',
        'button[aria-label*="dates" i]',
        '[placeholder="Add dates"]',
        'button:has-text("Add dates")',
    ]

    def _picker_is_open(self, timeout_ms: int = 3000) -> bool:
        """Check if the calendar date picker is currently visible."""
        try:
            picker_open = bool(self.page.evaluate("""
                () => {
                    const nextBtns = [...document.querySelectorAll(
                        'button[aria-label*="Move forward" i], button[aria-label*="next month" i], button[data-testid*="calendar-next"]'
                    )].filter(el => el.offsetParent !== null);

                    const dayBtns = [...document.querySelectorAll(
                        '[data-testid="datepicker-portal"] button[aria-label], div[role="dialog"] button[aria-label], table button[aria-label]'
                    )].filter(el => {
                        if (el.offsetParent === null) return false;
                        if (el.hasAttribute('disabled')) return false;
                        const label = (el.getAttribute('aria-label') || '').trim();
                        return label.length > 4;
                    });

                    return nextBtns.length > 0 || dayBtns.length >= 8;
                }
            """))
            if picker_open:
                print("  Date picker detected via calendar controls.")
                return True
        except Exception:
            pass

        for sel in self.DATEPICKER_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    print(f"  Date picker found via: {sel}")
                    return True
            except Exception:
                continue
        for sel in self.DATEPICKER_SELECTORS:
            try:
                self.page.wait_for_selector(sel, timeout=timeout_ms)
                print(f"  Date picker found (wait) via: {sel}")
                return True
            except Exception:
                continue
        return False

    def _destination_is_present(self) -> bool:
        try:
            return bool(self.page.evaluate("""
                () => {
                    const blocked = new Set(['where', 'search destinations']);
                    const selectors = [
                        '[data-testid="structured-search-input-field-query"]',
                        '[data-testid="structured-search-input-field-query-input"]',
                        'button[aria-label*="where" i]',
                        'input[name="query"]',
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (!el || el.offsetParent === null) continue;
                        const text = ((el.value || el.innerText || el.textContent || '') + '').trim().toLowerCase();
                        if (text && !blocked.has(text)) return true;
                    }
                    return false;
                }
            """))
        except Exception:
            return False

    def _restore_destination_if_needed(self) -> bool:
        if self._destination_is_present():
            return True

        destination = self.shared_state.get("chosen_suggestion") or self.shared_state.get("selected_country")
        if not destination:
            return False

        print(f"  Destination missing — restoring '{destination}' from checkpoint.")
        trigger_selectors = [
            '[data-testid="structured-search-input-field-query"]',
            'button[aria-label*="where" i]',
            'button:has-text("Where")',
            'button:has-text("Search destinations")',
        ]
        input_selectors = [
            'input[data-testid="structured-search-input-field-query-input"]',
            '[placeholder="Search destinations"]',
            'input[name="query"]',
            'input[aria-autocomplete="list"]',
        ]

        for sel in trigger_selectors:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    loc.click()
                    time.sleep(0.4)
                    break
            except Exception:
                continue

        for sel in input_selectors:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    loc.click()
                    self.page.keyboard.press("Control+a")
                    self.page.keyboard.press("Backspace")
                    self.page.keyboard.type(destination)
                    time.sleep(0.5)
                    self.page.keyboard.press("ArrowDown")
                    time.sleep(0.2)
                    self.page.keyboard.press("Enter")
                    time.sleep(1.2)
                    return self._destination_is_present()
            except Exception:
                continue

        # "Copy-paste" style fallback: set input value via JS and dispatch input/change.
        try:
            pasted = bool(self.page.evaluate(
                """
                (payload) => {
                    const { value, selectors } = payload;
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (!el || el.offsetParent === null) continue;
                        el.focus();
                        el.value = value;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        return true;
                    }
                    return false;
                }
                """,
                {"value": destination, "selectors": input_selectors},
            ))
            if pasted:
                time.sleep(0.4)
                try:
                    self.page.keyboard.press("ArrowDown")
                    time.sleep(0.2)
                    self.page.keyboard.press("Enter")
                    time.sleep(1.0)
                except Exception:
                    pass
                return self._destination_is_present()
        except Exception:
            pass

        return False

    def _open_date_picker(self) -> None:
        """Click the When/Add dates field to open the date picker."""
        for sel in self.WHEN_FIELD_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    print(f"  Clicked date field via: {sel}")
                    time.sleep(1.5)
                    return
            except Exception:
                continue
        # JS fallback
        try:
            self.page.evaluate("""
                () => {
                    const els = Array.from(document.querySelectorAll('div, button, span'));
                    const el = els.find(e =>
                        ((e.innerText || '').toLowerCase().includes('add dates') ||
                         (e.getAttribute('aria-label') || '').toLowerCase().includes('check in') ||
                         (e.getAttribute('aria-label') || '').toLowerCase().includes('dates')) &&
                        e.offsetParent !== null
                    );
                    if (el) el.click();
                }
            """)
            time.sleep(1.5)
        except Exception:
            pass

    def _click_next_month(self) -> bool:
        for sel in self.NEXT_MONTH_SELECTORS:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    loc.click(timeout=1500)
                    return True
            except Exception:
                continue

        try:
            clicked = self.page.evaluate("""
                () => {
                    const btn = [...document.querySelectorAll(
                        'button[aria-label*="Move forward" i], button[aria-label*="next month" i], button[data-testid*="calendar-next"]'
                    )].find(el => el.offsetParent !== null);
                    if (btn) { btn.click(); return true; }
                    return false;
                }
            """)
            return bool(clicked)
        except Exception:
            return False

        return False

    def _get_day_buttons(self) -> list:
        """Return all clickable (enabled) day buttons in the visible calendar."""
        for sel in [
            '[data-testid="datepicker-portal"] button[aria-label]:not([disabled])',
            'div[role="dialog"] button[aria-label]:not([disabled])',
            'td[aria-disabled="false"] button',
            'td:not([aria-disabled="true"]) button',
            'table td button:not([disabled])',
        ]:
            try:
                days = self.page.query_selector_all(sel)
                filtered = []
                for day in days:
                    try:
                        if not day.is_visible():
                            continue
                        label = (day.get_attribute("aria-label") or "").strip()
                        if label or day.inner_text().strip():
                            filtered.append(day)
                    except Exception:
                        continue
                if filtered:
                    return filtered
            except Exception:
                continue
        return []

    def _get_date_field_value(self, field_selector: str) -> str:
        """Read the current value of a date input field."""
        try:
            el = self.page.query_selector(field_selector)
            if el:
                return el.inner_text().strip() or el.input_value()
        except Exception:
            pass
        return ""

    def _read_visible_month_label(self) -> str:
        for sel in ['h2[aria-live="polite"]', '[data-testid="calendar-heading"]', 'h2']:
            try:
                for el in self.page.query_selector_all(sel):
                    text = (el.inner_text() or "").strip()
                    if any(m in text for m in [
                        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
                    ]):
                        return text
            except Exception:
                continue
        return ""

    @staticmethod
    def _is_real_date_value(value: str) -> bool:
        normalized = (value or "").strip().lower()
        if not normalized:
            return False
        blocked = {"add dates", "check in", "check out", "dates"}
        return normalized not in blocked

    def _ensure_picker_open(self, attempts: int = 4) -> bool:
        for _ in range(attempts):
            if self._picker_is_open(timeout_ms=1200):
                return True
            self._open_date_picker()
            time.sleep(0.8)
            if self._picker_is_open(timeout_ms=1200):
                return True
            self._restore_destination_if_needed()
        return False

    def run(self) -> ResultModel:
        print("\n[Step 03] Date Picker Interaction...")
        time.sleep(2)
        self.restore_checkpoint()
        self.safe_dismiss_popups()
        destination_ok = self._restore_destination_if_needed()
        print(f"  Destination ready for Step 03: {destination_ok}")
        if not destination_ok:
            screenshot_path = self.screenshot("step03_destination_missing")
            return self.save(
                False,
                "Destination missing before Step 03 and restore from checkpoint failed.",
                screenshot_path,
            )

        max_selection_attempts = 8
        picker_visible = False
        month_label = ""
        checkin_date = ""
        checkout_date = ""
        checkin_field_val = ""
        checkout_field_val = ""
        dates_ok = False

        for attempt in range(max_selection_attempts):
            print(f"  Date selection attempt {attempt + 1}/{max_selection_attempts}...")
            picker_visible = self._ensure_picker_open(attempts=4)
            if not picker_visible:
                print("  Date picker not found in this attempt.")
                continue

            next_clicks = random.randint(2, 4)
            moved = 0
            for _ in range(next_clicks):
                if self._click_next_month():
                    moved += 1
                    time.sleep(0.5)
                else:
                    # Modal can disappear after internal Airbnb refresh/state reset.
                    if not self._ensure_picker_open(attempts=2):
                        break
            month_label = self._read_visible_month_label() or month_label
            print(f"  Visible month: {month_label} (moved {moved}/{next_clicks})")

            days = self._get_day_buttons()
            print(f"  Available day buttons: {len(days)}")
            if len(days) < 2:
                continue

            checkin_idx = min(4, len(days) - 2)
            checkout_idx = min(checkin_idx + 4, len(days) - 1)
            if checkout_idx <= checkin_idx and len(days) >= 2:
                checkout_idx = min(checkin_idx + 1, len(days) - 1)

            try:
                checkin_el = days[checkin_idx]
                checkin_date = checkin_el.get_attribute("aria-label") or checkin_el.inner_text().strip()
                checkin_el.click()
                time.sleep(0.9)
                print(f"  Check-in selected: {checkin_date}")
            except Exception as exc:
                print(f"  Check-in click failed: {exc}")
                continue

            if not self._ensure_picker_open(attempts=2):
                self._open_date_picker()
                time.sleep(0.6)

            days = self._get_day_buttons()
            if len(days) < 2:
                continue

            checkout_idx = min(checkout_idx, len(days) - 1)
            try:
                checkout_el = days[checkout_idx]
                checkout_date = checkout_el.get_attribute("aria-label") or checkout_el.inner_text().strip()
                checkout_el.click()
                time.sleep(1.0)
                print(f"  Check-out selected: {checkout_date}")
            except Exception as exc:
                print(f"  Check-out click failed: {exc}")
                continue

            checkin_field_val = self._get_date_field_value(
                '[data-testid="structured-search-input-field-split-dates-0"]'
            )
            checkout_field_val = self._get_date_field_value(
                '[data-testid="structured-search-input-field-split-dates-1"]'
            )
            print(f"  Check-in field shows: '{checkin_field_val}'")
            print(f"  Check-out field shows: '{checkout_field_val}'")

            dates_ok = (
                self._is_real_date_value(checkin_field_val)
                and self._is_real_date_value(checkout_field_val)
            )
            if dates_ok:
                # Store the field values for later restore/matching because those
                # are what Airbnb actually applies to the current search context.
                checkin_date = checkin_field_val
                checkout_date = checkout_field_val
                break

            print("  Date fields still empty/invalid after selection, retrying...")

        screenshot_path = self.screenshot("step03_datepicker_open")
        screenshot_path2 = self.screenshot("step03_dates_selected")

        if not picker_visible:
            return self.save(
                False,
                "Date picker modal could not be found after repeated retries.",
                screenshot_path,
            )

        self.shared_state["selected_month"] = month_label
        self.shared_state["checkin_date"] = checkin_date
        self.shared_state["checkout_date"] = checkout_date
        if dates_ok:
            self.checkpoint("step03_dates_selected")

        comment = (
            f"Date picker recovered with retries. Visible month: {month_label}. "
            f"Check-in: {checkin_date}, Check-out: {checkout_date}. "
            f"Fields show — checkin: '{checkin_field_val}', checkout: '{checkout_field_val}'."
        )
        return self.save(dates_ok, comment, screenshot_path2)
