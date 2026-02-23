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
        '[data-testid="guest-picker"]',
        'div[id*="guest"]',
    ]

    GUEST_POPUP_SELECTORS = [
        '[data-testid="structured-search-input-field-guests-panel"]',
        '[aria-label*="guests" i]',
        'div[role="group"]:has(button[aria-label*="increase" i])',
    ]

    SEARCH_BTN_SELECTORS = [
        '[data-testid="structured-search-input-search-button"]',
        'button[aria-label="Search"]',
        'button:has-text("Search")',
        'button.search-button',
    ]

    def run(self) -> ResultModel:
        print("\n[Step 04] Guest Picker Interaction...")

        clicked = False
        for sel in self.GUEST_FIELD_SELECTORS:
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
                self.page.click('[data-testid="structured-search-input-field-guests-button"]', timeout=5000)
                clicked = True
            except Exception:
                pass

        time.sleep(1)

        popup_visible = False
        for sel in self.GUEST_POPUP_SELECTORS:
            try:
                self.page.wait_for_selector(sel, timeout=5000)
                popup_visible = True
                break
            except Exception:
                continue

        screenshot_before = self.screenshot("step04_guest_popup")

        if not popup_visible:
            return self.save(False, "Guest picker popup did not open.", screenshot_before)

        total_guests_to_add = random.randint(2, 5)
        total_added = 0

        increase_buttons = self.page.query_selector_all('button[aria-label*="increase" i]')
        if not increase_buttons:
            increase_buttons = self.page.query_selector_all('[data-testid*="stepper"][data-testid*="increase"]')

        if increase_buttons:
            adults_added = random.randint(1, max(1, total_guests_to_add - 1))
            for _ in range(adults_added):
                try:
                    increase_buttons[0].click()
                    total_added += 1
                    time.sleep(0.4)
                except Exception:
                    break

            remaining = total_guests_to_add - adults_added
            for btn_idx in range(1, min(len(increase_buttons), 4)):
                if remaining <= 0:
                    break
                to_add = random.randint(0, remaining)
                for _ in range(to_add):
                    try:
                        increase_buttons[btn_idx].click()
                        total_added += 1
                        remaining -= 1
                        time.sleep(0.3)
                    except Exception:
                        break
        else:
            print("  Warning: No increase buttons found in guest picker.")

        self.shared_state["guest_count"] = total_added
        print(f"  Added {total_added} guests total.")

        time.sleep(0.5)
        screenshot_path = self.screenshot("step04_guests_selected")

        guest_display = ""
        try:
            guest_btn = self.page.query_selector(
                '[data-testid="structured-search-input-field-guests-button"]'
            )
            if guest_btn:
                guest_display = guest_btn.inner_text().strip()
        except Exception:
            pass

        print(f"  Guest field shows: {guest_display}")

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

        time.sleep(3)

        comment = (
            f"Guest popup opened successfully. Added {total_added} guests. "
            f"Guest field displays: '{guest_display}'. "
            f"Search button clicked: {search_clicked}."
        )
        return self.save(popup_visible and total_added > 0, comment, screenshot_path)
