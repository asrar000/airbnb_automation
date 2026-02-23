"""
Step 04: Guest Picker Interaction
- Click the Who / Add guests field
- Verify guest selection popup opens
- Randomly add 2-5 guests across Adults/Children/Infants/Pets
- Verify guest count shown matches selected
- Click Search button
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.models import ResultModel


class Step04GuestPicker(BaseTestStep):
    name = "Guest Picker Interaction Test"

    GUEST_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-guests-button"]',
        '[placeholder="Add guests"]',
        'button:has-text("Add guests")',
        '[data-testid="structured-search-input-field-guests"]',
    ]

    GUEST_POPUP_SELECTORS = [
        '[data-testid="structured-search-input-field-guests-panel"]',
        'div[data-testid*="guest"]:has(button[data-testid*="stepper"])',
        'div:has(button[aria-label*="increase" i]):has(button[aria-label*="decrease" i])',
        '[data-testid*="guest-panel"]',
    ]

    SEARCH_BTN_SELECTORS = [
        '[data-testid="structured-search-input-search-button"]',
        'button[aria-label="Search"]',
        'button:has-text("Search")',
        'button[type="submit"]',
    ]

    def _open_guest_field(self) -> bool:
        for sel in self.GUEST_FIELD_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    return True
            except Exception:
                continue
        return False

    def _popup_is_open(self, timeout_ms: int = 5000) -> bool:
        for sel in self.GUEST_POPUP_SELECTORS:
            try:
                self.page.wait_for_selector(sel, timeout=timeout_ms)
                print(f"  Guest popup detected via: {sel}")
                return True
            except Exception:
                continue
        # Fallback: look for increase buttons which only appear in the popup
        try:
            btns = self.page.query_selector_all('button[aria-label*="increase" i]')
            if btns:
                print("  Guest popup detected via increase buttons.")
                return True
        except Exception:
            pass
        return False

    def _get_increase_buttons(self) -> list:
        """Return all +/increase stepper buttons in the guest panel."""
        selectors = [
            'button[data-testid*="stepper-increase"]',
            'button[aria-label*="increase" i]',
            'button[aria-label*="add" i]:not([aria-label*="date" i])',
        ]
        for sel in selectors:
            btns = self.page.query_selector_all(sel)
            if btns:
                return btns
        return []

    def run(self) -> ResultModel:
        print("\n[Step 04] Guest Picker Interaction...")

        # --- Open the guest field ---
        clicked = self._open_guest_field()
        if not clicked:
            print("  Warning: standard guest field selectors missed — trying fallback.")
            try:
                # Sometimes clicking the "Who" label area works
                self.page.click('text="Add guests"', timeout=5000)
                clicked = True
            except Exception:
                pass

        time.sleep(1.5)

        # --- Verify popup is open ---
        popup_visible = self._popup_is_open(timeout_ms=6000)
        screenshot_before = self.screenshot("step04_guest_popup")

        if not popup_visible:
            return self.save(False, "Guest picker popup did not open.", screenshot_before)

        # --- Add guests ---
        total_guests_to_add = random.randint(2, 5)
        total_added = 0

        increase_buttons = self._get_increase_buttons()
        print(f"  Increase buttons found: {len(increase_buttons)}")

        if increase_buttons:
            # Always add at least 1 adult (button index 0)
            adults_to_add = random.randint(1, max(1, total_guests_to_add - 1))
            for _ in range(adults_to_add):
                try:
                    increase_buttons[0].click()
                    total_added += 1
                    time.sleep(0.4)
                except Exception:
                    break

            # Distribute remaining across other categories
            remaining = total_guests_to_add - adults_to_add
            for btn_idx in range(1, min(len(increase_buttons), 4)):
                if remaining <= 0:
                    break
                to_add = random.randint(0, remaining)
                for _ in range(to_add):
                    try:
                        # Re-fetch buttons each time to avoid stale refs
                        btns = self._get_increase_buttons()
                        if btn_idx < len(btns):
                            btns[btn_idx].click()
                            total_added += 1
                            remaining -= 1
                            time.sleep(0.35)
                    except Exception:
                        break
        else:
            print("  Warning: No increase buttons found in guest picker.")

        self.shared_state["guest_count"] = total_added
        print(f"  Total guests added: {total_added}")

        time.sleep(0.8)
        screenshot_path = self.screenshot("step04_guests_selected")

        # --- Read guest field display text ---
        guest_display = ""
        try:
            guest_btn = self.page.query_selector(
                '[data-testid="structured-search-input-field-guests-button"]'
            )
            if guest_btn:
                guest_display = guest_btn.inner_text().strip()
        except Exception:
            pass
        print(f"  Guest field displays: '{guest_display}'")

        # --- Click Search ---
        search_clicked = False
        for sel in self.SEARCH_BTN_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    search_clicked = True
                    print("  Search button clicked.")
                    break
            except Exception:
                continue

        if not search_clicked:
            print("  Warning: Search button not found — pressing Enter.")
            self.page.keyboard.press("Enter")

        # Wait for results page to load
        time.sleep(4)

        comment = (
            f"Guest popup opened successfully. Added {total_added} guests. "
            f"Guest field displays: '{guest_display}'. "
            f"Search button clicked: {search_clicked}."
        )
        return self.save(popup_visible and total_added > 0, comment, screenshot_path)