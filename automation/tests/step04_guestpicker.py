"""
Step 04: Guest Picker Interaction Test

After Step 03 selects dates, Airbnb shows the guest picker field.
This step:
- Clicks the Who / Add guests field
- Verifies the guest selection popup opens
- Randomly adds 2-5 guests across Adults/Children/Infants/Pets
- Verifies the displayed guest count matches selected values
- Clicks the Search button to navigate to results (Step 05)
"""
import random
import re
import time

from automation.tests.base import BaseTestStep
from automation.db_logger import run_in_thread
from automation.models import ResultModel


class Step04GuestPicker(BaseTestStep):
    name = "Guest Picker Interaction Test"
    STEP03_RESULT_NAME = "Date Picker Modal Open and Visibility Test"

    DATE_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-split-dates-0"]',
        '[data-testid="structured-search-input-field-split-dates-1"]',
        '[data-testid="structured-search-input-field-dates-button"]',
        'button[aria-label*="check in" i]',
        'button[aria-label*="dates" i]',
        'button:has-text("Add dates")',
    ]

    NEXT_MONTH_SELECTORS = [
        '[aria-label*="Move forward" i]',
        'button[aria-label*="next month" i]',
        'button[data-testid*="calendar-next"]',
    ]

    GUEST_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-guests-button"]',
        '[placeholder="Add guests"]',
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
                    print(f"  Guest field clicked via: {sel}")
                    return True
            except Exception:
                continue
        # JS fallback
        try:
            clicked = self.page.evaluate("""
                () => {
                    const els = Array.from(document.querySelectorAll('div, button'));
                    const el = els.find(e =>
                        (e.innerText || '').trim().includes('Add guests') &&
                        e.offsetParent !== null
                    );
                    if (el) { el.click(); return true; }
                    return false;
                }
            """)
            if clicked:
                print("  Guest field clicked via JS.")
                return True
        except Exception:
            pass
        return False

    def _popup_is_open(self) -> bool:
        """Confirm popup is open by checking stepper increase buttons are visible."""
        try:
            found = self.page.evaluate("""
                () => {
                    const btns = document.querySelectorAll(
                        'button[data-testid*="stepper-increase"], button[aria-label*="increase" i]'
                    );
                    for (const btn of btns) {
                        if (btn.offsetParent !== null) return true;
                    }
                    return false;
                }
            """)
            if found:
                print("  Guest popup open — stepper buttons visible.")
                return True
        except Exception:
            pass
        return False

    def _get_increase_buttons(self) -> list:
        for sel in [
            'button[data-testid*="stepper-increase"]',
            'button[aria-label*="increase" i]',
        ]:
            btns = self.page.query_selector_all(sel)
            if btns:
                return list(btns)
        return []

    def _get_guest_display(self) -> str:
        """Read the current guest count text from the guest field."""
        try:
            el = self.page.query_selector(
                '[data-testid="structured-search-input-field-guests-button"]'
            )
            if el:
                return el.inner_text().strip()
        except Exception:
            pass
        return ""

    def _read_date_field_values(self) -> tuple[str, str]:
        checkin_text = ""
        checkout_text = ""
        try:
            el = self.page.query_selector('[data-testid="structured-search-input-field-split-dates-0"]')
            if el:
                checkin_text = (el.inner_text() or "").strip()
        except Exception:
            pass
        try:
            el = self.page.query_selector('[data-testid="structured-search-input-field-split-dates-1"]')
            if el:
                checkout_text = (el.inner_text() or "").strip()
        except Exception:
            pass
        return checkin_text, checkout_text

    def _dates_present_in_ui(self) -> bool:
        checkin_text, checkout_text = self._read_date_field_values()
        blocked = {"", "add dates", "check in", "check out"}
        checkin_ok = checkin_text.strip().lower() not in blocked
        checkout_ok = checkout_text.strip().lower() not in blocked
        return checkin_ok and checkout_ok

    def _open_date_picker(self) -> bool:
        for sel in self.DATE_FIELD_SELECTORS:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    loc.click()
                    time.sleep(0.8)
                    return True
            except Exception:
                continue
        try:
            clicked = bool(self.page.evaluate("""
                () => {
                    const els = [...document.querySelectorAll('button, div, span')];
                    const el = els.find(e => {
                        if (e.offsetParent === null) return false;
                        const text = (e.innerText || '').toLowerCase();
                        const aria = (e.getAttribute('aria-label') || '').toLowerCase();
                        return text.includes('add dates') || aria.includes('check in') || aria.includes('dates');
                    });
                    if (!el) return false;
                    el.click();
                    return true;
                }
            """))
            if clicked:
                time.sleep(0.8)
            return clicked
        except Exception:
            return False

    def _ensure_dates_tab_selected(self) -> bool:
        try:
            ensured = bool(self.page.evaluate("""
                () => {
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        return !!r && r.width > 0 && r.height > 0;
                    };
                    const isActive = (el) => {
                        const ariaSelected = norm(el.getAttribute('aria-selected')) === 'true';
                        const ariaPressed = norm(el.getAttribute('aria-pressed')) === 'true';
                        const cls = norm((el.className || '').toString());
                        return ariaSelected || ariaPressed || cls.includes('selected') || cls.includes('active');
                    };

                    const tabs = [...document.querySelectorAll('button, [role="tab"], div[role="tab"], span[role="tab"]')]
                        .filter((el) => {
                            if (!isVisible(el)) return false;
                            const text = norm(el.innerText || el.textContent);
                            const aria = norm(el.getAttribute('aria-label'));
                            return text === 'dates' || text.startsWith('dates ') || aria === 'dates' || aria.includes('dates');
                        });
                    if (!tabs.length) return true;
                    if (tabs.some(isActive)) return true;
                    tabs[0].click();
                    return true;
                }
            """))
            if ensured:
                time.sleep(0.3)
            return ensured
        except Exception:
            return False

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

    def _click_next_month(self) -> bool:
        for sel in self.NEXT_MONTH_SELECTORS:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    loc.click(timeout=1200)
                    return True
            except Exception:
                continue
        return False

    def _move_to_saved_month(self) -> bool:
        target_month = (self.shared_state.get("selected_month") or "").strip()
        if not target_month:
            return True

        for _ in range(12):
            visible = self._read_visible_month_label()
            if visible and target_month.lower() in visible.lower():
                return True
            if not self._click_next_month():
                break
            time.sleep(0.4)
        return False

    @staticmethod
    def _extract_date_tokens(date_label: str) -> dict:
        month_match = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)",
            date_label or "",
            re.IGNORECASE,
        )
        day_match = re.search(r"\b([0-3]?\d)\b", date_label or "")
        year_match = re.search(r"\b(20\d{2})\b", date_label or "")
        return {
            "raw": date_label or "",
            "month": month_match.group(1) if month_match else "",
            "day": day_match.group(1).lstrip("0") if day_match else "",
            "year": year_match.group(1) if year_match else "",
        }

    def _click_saved_date(self, saved_label: str) -> bool:
        tokens = self._extract_date_tokens(saved_label)
        try:
            return bool(self.page.evaluate(
                """
                (payload) => {
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const raw = norm(payload.raw);
                    const month = norm(payload.month);
                    const day = (payload.day || '').trim();
                    const year = (payload.year || '').trim();

                    const buttons = [...document.querySelectorAll(
                        '[data-testid="datepicker-portal"] button[aria-label], div[role="dialog"] button[aria-label], table button[aria-label]'
                    )].filter(el => el.offsetParent !== null && !el.hasAttribute('disabled'));

                    let target = null;

                    if (raw) {
                        target = buttons.find(b => norm(b.getAttribute('aria-label')) === raw);
                    }
                    if (!target && raw) {
                        target = buttons.find(b => norm(b.getAttribute('aria-label')).includes(raw));
                    }
                    if (!target && day) {
                        const dayRegex = new RegExp(`\\\\b0?${day}\\\\b`);
                        target = buttons.find(b => {
                            const label = norm(b.getAttribute('aria-label'));
                            if (month && !label.includes(month)) return false;
                            if (year && !label.includes(year)) return false;
                            return dayRegex.test(label);
                        });
                    }
                    if (!target) return false;
                    target.click();
                    return true;
                }
                """,
                tokens,
            ))
        except Exception:
            return False

    def _restore_dates_if_needed(self) -> bool:
        if self._dates_present_in_ui():
            return True

        checkin_saved = self.shared_state.get("checkin_date", "")
        checkout_saved = self.shared_state.get("checkout_date", "")
        if not (checkin_saved and checkout_saved):
            restored = self._restore_context_from_db()
            if restored:
                print("  Restored location/dates from DB backup.")
                self.checkpoint("step04_context_restored_from_db")
                checkin_saved = self.shared_state.get("checkin_date", "")
                checkout_saved = self.shared_state.get("checkout_date", "")
        if not (checkin_saved and checkout_saved):
            return False

        print("  Dates missing — restoring from checkpoint.")
        if not self._open_date_picker():
            return False

        self._ensure_dates_tab_selected()
        self._move_to_saved_month()
        self._ensure_dates_tab_selected()

        if not self._click_saved_date(checkin_saved):
            return False
        time.sleep(0.5)

        if not self._click_saved_date(checkout_saved):
            return False
        time.sleep(0.8)

        return self._dates_present_in_ui()

    def _restore_context_from_db(self) -> bool:
        """
        Fallback when checkpoint/shared_state are missing after refresh.
        Uses the latest passed Step 03 row to restore location + dates.
        """
        try:
            payload = run_in_thread(
                lambda: ResultModel.objects.filter(
                    test_case=self.STEP03_RESULT_NAME,
                    passed=True,
                )
                .order_by("-created_at")
                .values(
                    "selected_location",
                    "selected_month",
                    "checkin_date",
                    "checkout_date",
                )
                .first()
            )
        except Exception:
            return False

        if not payload:
            return False

        restored = False
        selected_location = (payload.get("selected_location") or "").strip()
        selected_month = (payload.get("selected_month") or "").strip()
        checkin_date = (payload.get("checkin_date") or "").strip()
        checkout_date = (payload.get("checkout_date") or "").strip()

        if selected_location:
            if not self.shared_state.get("selected_location"):
                self.shared_state["selected_location"] = selected_location
                restored = True
            if not self.shared_state.get("selected_country"):
                self.shared_state["selected_country"] = selected_location
                restored = True
            if not self.shared_state.get("chosen_suggestion"):
                self.shared_state["chosen_suggestion"] = selected_location
                restored = True
        if selected_month and not self.shared_state.get("selected_month"):
            self.shared_state["selected_month"] = selected_month
            restored = True
        if checkin_date and not self.shared_state.get("checkin_date"):
            self.shared_state["checkin_date"] = checkin_date
            restored = True
        if checkout_date and not self.shared_state.get("checkout_date"):
            self.shared_state["checkout_date"] = checkout_date
            restored = True

        return restored

    def run(self) -> ResultModel:
        print("\n[Step 04] Guest Picker Interaction...")
        time.sleep(1)
        self.restore_checkpoint()
        self.safe_dismiss_popups()

        dates_ready = self._restore_dates_if_needed()
        print(f"  Dates ready for Step 04: {dates_ready}")
        if not dates_ready:
            screenshot_path = self.screenshot("step04_dates_missing")
            return self.save(
                False,
                "Step 04 requires dates from Step 03, but date restore failed.",
                screenshot_path,
            )
        self.checkpoint("step04_dates_verified")

        # Click the guest input field
        self._open_guest_field()
        time.sleep(1.5)

        # Wait for the popup to open
        popup_visible = False
        for attempt in range(6):
            if self._popup_is_open():
                popup_visible = True
                break
            print(f"  Waiting for guest popup... attempt {attempt + 1}")
            time.sleep(1)

        screenshot_before = self.screenshot("step04_guest_popup")

        if not popup_visible:
            return self.save(False, "Guest picker popup did not open.", screenshot_before)

        # Randomly select 2-5 guests distributed across categories
        total_to_add = random.randint(2, 5)
        total_added = 0
        added_counts = {"adults": 0, "children": 0, "infants": 0, "pets": 0}
        increase_buttons = self._get_increase_buttons()
        print(f"  Increase buttons found: {len(increase_buttons)}, Target guests: {total_to_add}")

        if increase_buttons:
            # Always add at least 1 adult
            adults = random.randint(1, max(1, total_to_add - 1))
            for _ in range(adults):
                try:
                    increase_buttons[0].click()
                    total_added += 1
                    added_counts["adults"] += 1
                    time.sleep(0.4)
                except Exception:
                    break

            # Distribute remaining across other categories (children, infants, pets)
            remaining = total_to_add - adults
            idx_to_key = {1: "children", 2: "infants", 3: "pets"}
            for btn_idx in range(1, min(len(increase_buttons), 4)):
                if remaining <= 0:
                    break
                to_add = random.randint(0, remaining)
                for _ in range(to_add):
                    try:
                        # Re-query each time to avoid stale element references
                        btns = self._get_increase_buttons()
                        if btn_idx < len(btns):
                            btns[btn_idx].click()
                            total_added += 1
                            key = idx_to_key.get(btn_idx)
                            if key:
                                added_counts[key] += 1
                            remaining -= 1
                            time.sleep(0.35)
                    except Exception:
                        break

            # Guarantee the requested 2-5 random additions even when the random
            # split above leaves remainder unassigned.
            while remaining > 0:
                btns = self._get_increase_buttons()
                usable = list(range(min(len(btns), 4)))
                if not usable:
                    break
                random.shuffle(usable)
                clicked_any = False
                for btn_idx in usable:
                    try:
                        btns[btn_idx].click()
                        total_added += 1
                        if btn_idx == 0:
                            added_counts["adults"] += 1
                        else:
                            key = idx_to_key.get(btn_idx)
                            if key:
                                added_counts[key] += 1
                        remaining -= 1
                        clicked_any = True
                        time.sleep(0.3)
                        break
                    except Exception:
                        continue
                if not clicked_any:
                    break

        # Airbnb "guests" typically means adults + children (infants/pets separate).
        search_guest_count = added_counts["adults"] + added_counts["children"]
        self.shared_state["guest_count"] = search_guest_count
        self.shared_state["guest_breakdown"] = added_counts
        self.shared_state["guest_total_added"] = total_added
        self.checkpoint("step04_guests_selected")
        print(
            "  Guest breakdown: "
            f"adults={added_counts['adults']}, "
            f"children={added_counts['children']}, "
            f"infants={added_counts['infants']}, pets={added_counts['pets']}"
        )
        print(f"  Search guest count (adults+children): {search_guest_count}")
        time.sleep(0.8)

        screenshot_path = self.screenshot("step04_guests_selected")

        # Verify displayed guest count matches selected values
        guest_display = self._get_guest_display()
        print(f"  Guest field displays: '{guest_display}'")
        displayed_guest_count = self._extract_first_int(guest_display) or 0
        guest_count_matches = displayed_guest_count == search_guest_count
        guest_display_lower = (guest_display or "").lower()
        extras_visible = True
        if added_counts["infants"] > 0 and "infant" not in guest_display_lower:
            extras_visible = False
        if added_counts["pets"] > 0 and "pet" not in guest_display_lower:
            extras_visible = False
        print(
            "  Guest count verification: "
            f"displayed={displayed_guest_count}, expected={search_guest_count}, "
            f"match={guest_count_matches}, extras_visible={extras_visible}"
        )

        # Click the Search button — triggers navigation to results page (Step 05)
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
            # JS fallback
            try:
                self.page.evaluate("""
                    () => {
                        const btn = document.querySelector(
                            '[data-testid="structured-search-input-search-button"]'
                        );
                        if (btn) btn.click();
                    }
                """)
                search_clicked = True
                print("  Search clicked via JS fallback.")
            except Exception:
                pass

        # Wait for navigation to results page
        time.sleep(5)

        comment = (
            f"Guest popup opened. Added total {total_added} across categories "
            f"(adults={added_counts['adults']}, children={added_counts['children']}, "
            f"infants={added_counts['infants']}, pets={added_counts['pets']}). "
            f"Search guest count: {search_guest_count}. "
            f"Field shows: '{guest_display}' (displayed count: {displayed_guest_count}, "
            f"matches selected: {guest_count_matches}, extras visible: {extras_visible}). "
            f"Search clicked: {search_clicked}."
        )
        passed = popup_visible and total_added >= 2 and guest_count_matches and extras_visible and search_clicked
        return self.save(passed, comment, screenshot_path)
