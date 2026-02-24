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
from datetime import date

from automation.tests.base import BaseTestStep
from automation.db_logger import run_in_thread
from automation.models import ResultModel


class Step04GuestPicker(BaseTestStep):
    name = "Guest Picker Interaction Test"
    STEP03_RESULT_NAME = "Date Picker Modal Open and Visibility Test"

    DATE_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-split-dates-0"]',
        '[data-testid="structured-search-input-field-split-dates-1"]',
        '[data-testid*="structured-search-input-field-split-dates"]',
        '[data-testid="structured-search-input-field-dates-button"]',
        '[data-testid*="structured-search-input-field-dates"]',
        'div[role="button"][aria-expanded][style*="grid-column: center"]',
        '[role="button"][aria-expanded]:has-text("When")',
        '[role="button"]:has-text("When")',
        '[role="button"]:has-text("Add dates")',
        'div[role="button"]:has-text("When")',
        'button[aria-label*="check in" i]',
        'button[aria-label*="check out" i]',
        'button[aria-label*="dates" i]',
        'button[aria-label*="when" i]',
        'button:has-text("When")',
        'button:has-text("Add dates")',
    ]

    NEXT_MONTH_SELECTORS = [
        '[aria-label*="Move forward" i]',
        'button[aria-label*="next month" i]',
        'button[data-testid*="calendar-next"]',
    ]

    GUEST_FIELD_SELECTORS = [
        '[role="button"][aria-expanded]:has-text("Who"):has-text("Add guests")',
        '[role="button"][aria-expanded]:has-text("Add guests")',
        'div[role="button"][aria-expanded][style*="grid-column: last"]',
        '[data-testid="structured-search-input-field-guests-button"]',
        '[data-testid*="structured-search-input-field-guests"]',
        '[data-testid*="guests-button"]',
        'button[aria-label*="who" i]',
        'button[aria-label*="guests" i]',
        'button:has-text("Who")',
        'button:has-text("Add guests")',
        '[placeholder="Add guests"]',
    ]

    SEARCH_BTN_SELECTORS = [
        '[data-testid="structured-search-input-search-button"]',
        'button[aria-label="Search"]',
        '[role="button"]:has-text("Search")',
        'button:has(div:has-text("Search"))',
        'button:has-text("Search")',
        'div.s15knsuf:has-text("Search")',
        'button[type="submit"]',
    ]

    GUEST_POPUP_ROW_SELECTORS = [
        '[data-testid="search-block-filter-stepper-row-adults"]',
        '[data-testid="search-block-filter-stepper-row-children"]',
        '[data-testid="search-block-filter-stepper-row-infants"]',
        '[data-testid="search-block-filter-stepper-row-pets"]',
        '[data-testid="stepper-adults-value"]',
        '[data-testid="stepper-children-value"]',
        '[data-testid="stepper-infants-value"]',
        '[data-testid="stepper-pets-value"]',
        '#searchFlow-title-label-adults',
        '#searchFlow-title-label-children',
        '#searchFlow-title-label-infants',
        '#searchFlow-title-label-pets',
    ]

    STEPPER_INCREASE_SELECTORS = {
        "adults": 'button[data-testid="stepper-adults-increase-button"]',
        "children": 'button[data-testid="stepper-children-increase-button"]',
        "infants": 'button[data-testid="stepper-infants-increase-button"]',
        "pets": 'button[data-testid="stepper-pets-increase-button"]',
    }

    STEPPER_DECREASE_SELECTORS = {
        "adults": 'button[data-testid="stepper-adults-decrease-button"]',
        "children": 'button[data-testid="stepper-children-decrease-button"]',
        "infants": 'button[data-testid="stepper-infants-decrease-button"]',
        "pets": 'button[data-testid="stepper-pets-decrease-button"]',
    }

    STEPPER_VALUE_SELECTORS = {
        "adults": '[data-testid="stepper-adults-value"]',
        "children": '[data-testid="stepper-children-value"]',
        "infants": '[data-testid="stepper-infants-value"]',
        "pets": '[data-testid="stepper-pets-value"]',
    }

    MONTH_TOKEN_TO_NUMBER = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "sept": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }

    @staticmethod
    def _extract_first_int(text: str):
        match = re.search(r"\d+", text or "")
        if not match:
            return None
        try:
            return int(match.group(0))
        except Exception:
            return None

    def _guest_field_is_visible(self) -> bool:
        for sel in self.GUEST_FIELD_SELECTORS:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=300):
                    return True
            except Exception:
                continue
        try:
            return bool(self.page.evaluate("""
                () => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const nodes = [...document.querySelectorAll('[role="button"][aria-expanded], button, div[role="button"]')];
                    return nodes.some((el) => {
                        if (!isVisible(el)) return false;
                        const t = (el.innerText || el.textContent || '').trim().toLowerCase();
                        return t.includes('who') && t.includes('add guests');
                    });
                }
            """))
        except Exception:
            pass
        return False

    def _guest_trigger_expanded(self) -> bool:
        try:
            return bool(self.page.evaluate("""
                () => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const buttons = [...document.querySelectorAll('[role="button"][aria-expanded]')];
                    for (const el of buttons) {
                        if (!isVisible(el)) continue;
                        const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                        if (!(text.includes('who') || text.includes('guest'))) continue;
                        const expanded = (el.getAttribute('aria-expanded') || '').trim().toLowerCase();
                        if (expanded === 'true') return true;
                    }
                    return false;
                }
            """))
        except Exception:
            return False

    def _expand_compact_search_bar(self) -> bool:
        """
        Airbnb sometimes collapses the full search bar into a compact shell.
        Click known wrappers first so the 'Who / Add guests' field becomes interactive.
        """
        selectors = [
            '.fam02bu',
            '.fp9kp52',
            '[data-testid="structured-search-input-field-query"]',
            '[data-testid="structured-search-input-field-query-button"]',
            'button[aria-label*="start your search" i]',
            'button[aria-label*="where to" i]',
        ]
        expanded = False
        for sel in selectors:
            try:
                loc = self.page.locator(sel).first
                if not loc.is_visible(timeout=400):
                    continue
                loc.click()
                time.sleep(0.4)
                if self._guest_field_is_visible() or self._popup_is_open() or self._guest_trigger_expanded():
                    expanded = True
                    print(f"  Expanded search UI via: {sel}")
                    break
            except Exception:
                continue
        return expanded

    def _close_date_picker_if_open(self) -> None:
        if not self._picker_is_open():
            return
        for _ in range(3):
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                break
            time.sleep(0.35)
            if not self._picker_is_open():
                return
        try:
            self.page.mouse.click(20, 20)
            time.sleep(0.3)
        except Exception:
            pass

    def _open_guest_field(self) -> bool:
        self._close_date_picker_if_open()
        if not self._guest_field_is_visible():
            self._expand_compact_search_bar()

        # First: exact role-button trigger matching "Who / Add guests"
        try:
            clicked = bool(self.page.evaluate("""
                () => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const candidates = [...document.querySelectorAll('[role="button"][aria-expanded], div[role="button"], button')];
                    const target = candidates.find((el) => {
                        if (!isVisible(el)) return false;
                        const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                        return text.includes('who') && text.includes('add guests');
                    });
                    if (!target) return false;

                    for (const evt of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
                        target.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    }
                    target.click();
                    return true;
                }
            """))
            if clicked:
                time.sleep(0.35)
                if self._popup_is_open() or self._guest_trigger_expanded():
                    print("  Guest field clicked via role-button text match.")
                    return True
        except Exception:
            pass

        for sel in self.GUEST_FIELD_SELECTORS:
            try:
                loc = self.page.locator(sel).first
                if not loc.is_visible(timeout=500):
                    continue
                loc.click(timeout=1500)
                time.sleep(0.35)
                if self._popup_is_open() or self._guest_trigger_expanded():
                    print(f"  Guest field clicked via: {sel}")
                    return True
            except Exception:
                continue

        # JS fallback with clickable-ancestor resolution around "Who / Add guests".
        try:
            clicked = bool(self.page.evaluate("""
                () => {
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    };
                    const clickableParent = (node) => {
                        let cur = node;
                        for (let i = 0; i < 10 && cur; i += 1) {
                            if (
                                cur.matches?.('[role="button"][aria-expanded], button, [role="button"], a, [tabindex], [data-testid*="guests"], [data-testid*="who"], .fp9kp52, .fam02bu')
                            ) {
                                return cur;
                            }
                            cur = cur.parentElement;
                        }
                        return node;
                    };

                    const nodes = [...document.querySelectorAll('button, div, span')].filter(isVisible);
                    let target = null;

                    target = nodes.find((el) => {
                        const text = norm(el.innerText || el.textContent);
                        return text.includes('who') && text.includes('add guests');
                    });
                    if (!target) {
                        target = nodes.find((el) => norm(el.innerText || el.textContent).includes('add guests'));
                    }
                    if (!target) {
                        target = nodes.find((el) => {
                            const cls = norm(el.className);
                            return cls.includes('fp9kp52') || cls.includes('fam02bu');
                        });
                    }
                    if (!target) return false;

                    const clickNode = clickableParent(target);
                    for (const evt of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
                        clickNode.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    }
                    clickNode.click();
                    return true;
                }
            """))
            if clicked:
                time.sleep(0.4)
                if self._popup_is_open() or self._guest_trigger_expanded():
                    print("  Guest field clicked via JS.")
                    return True
        except Exception:
            pass
        return False

    def _location_is_present(self) -> bool:
        try:
            return bool(self.page.evaluate("""
                () => {
                    const blocked = new Set(['where', 'search destinations']);
                    const selectors = [
                        '[data-testid="structured-search-input-field-query"]',
                        '[data-testid="structured-search-input-field-query-input"]',
                        '#bigsearch-query-location-input',
                        'input[name="query"]',
                        'button[aria-label*="where" i]',
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (!el || el.offsetParent === null) continue;
                        const text = ((el.value || el.innerText || el.textContent || '') + '')
                            .replace(/\\s+/g, ' ')
                            .trim()
                            .toLowerCase();
                        if (text && !blocked.has(text)) return true;
                    }
                    return false;
                }
            """))
        except Exception:
            return False

    def _restore_location_if_needed(self) -> bool:
        if self._location_is_present():
            return True

        destination = (
            self.shared_state.get("selected_location")
            or self.shared_state.get("chosen_suggestion")
            or self.shared_state.get("selected_country")
            or ""
        ).strip()
        if not destination:
            if self._restore_context_from_db():
                destination = (
                    self.shared_state.get("selected_location")
                    or self.shared_state.get("chosen_suggestion")
                    or self.shared_state.get("selected_country")
                    or ""
                ).strip()
        if not destination:
            return False

        print(f"  Location missing — restoring '{destination}' from checkpoint.")
        self._expand_compact_search_bar()
        trigger_selectors = [
            '[data-testid="structured-search-input-field-query"]',
            'button[aria-label*="where" i]',
            'button:has-text("Where")',
            'button:has-text("Search destinations")',
        ]
        input_selectors = [
            'input[data-testid="structured-search-input-field-query-input"]',
            '#bigsearch-query-location-input',
            '[placeholder="Search destinations"]',
            'input[name="query"]',
            'input[aria-autocomplete="list"]',
        ]

        for sel in trigger_selectors:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    loc.click()
                    time.sleep(0.35)
                    break
            except Exception:
                continue

        for sel in input_selectors:
            try:
                loc = self.page.locator(sel).first
                if not loc.is_visible(timeout=500):
                    continue
                loc.click()
                self.page.keyboard.press("Control+a")
                self.page.keyboard.press("Backspace")
                self.page.keyboard.type(destination)
                time.sleep(0.45)
                self.page.keyboard.press("ArrowDown")
                time.sleep(0.2)
                self.page.keyboard.press("Enter")
                time.sleep(1.0)
                if self._location_is_present():
                    self.shared_state["selected_location"] = destination
                    return True
            except Exception:
                continue

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
                    time.sleep(0.8)
                except Exception:
                    pass
                if self._location_is_present():
                    self.shared_state["selected_location"] = destination
                    return True
        except Exception:
            pass

        # Final fallback: keep checkpoint value for downstream URL fallback even if UI probing fails.
        self.shared_state["selected_location"] = destination
        return bool(destination)

    def _popup_is_open(self) -> bool:
        """Confirm popup is open by checking stepper increase buttons are visible."""
        try:
            found = self.page.evaluate("""
                () => {
                    const selectors = [
                        'button[data-testid="stepper-adults-increase-button"]',
                        'button[data-testid="stepper-children-increase-button"]',
                        'button[data-testid="stepper-infants-increase-button"]',
                        'button[data-testid="stepper-pets-increase-button"]',
                        '[data-testid="search-block-filter-stepper-row-adults"]',
                        '[data-testid="search-block-filter-stepper-row-children"]',
                        '[data-testid="search-block-filter-stepper-row-infants"]',
                        '[data-testid="search-block-filter-stepper-row-pets"]',
                        '[data-testid="stepper-adults-value"]',
                        '[data-testid="stepper-children-value"]',
                        '[data-testid="stepper-infants-value"]',
                        '[data-testid="stepper-pets-value"]',
                        '#searchFlow-title-label-adults',
                        '#searchFlow-title-label-children',
                        '#searchFlow-title-label-infants',
                        '#searchFlow-title-label-pets',
                    ];
                    for (const sel of selectors) {
                        const nodes = document.querySelectorAll(sel);
                        for (const node of nodes) {
                            if (node.offsetParent !== null) return true;
                        }
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
        resolved = []
        for key in ["adults", "children", "infants", "pets"]:
            sel = self.STEPPER_INCREASE_SELECTORS[key]
            try:
                loc = self.page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=400):
                    resolved.append(loc)
            except Exception:
                continue
        return resolved

    def _click_stepper_increase(self, key: str) -> bool:
        sel = self.STEPPER_INCREASE_SELECTORS.get(key)
        if not sel:
            return False
        try:
            loc = self.page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=400):
                if loc.is_disabled():
                    return False
                loc.click(timeout=1200)
                return True
        except Exception:
            pass
        try:
            return bool(self.page.evaluate(
                """
                (selector) => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const nodes = [...document.querySelectorAll(selector)].filter(isVisible);
                    const el = nodes.find((n) => {
                        if (n.hasAttribute('disabled')) return false;
                        return (n.getAttribute('aria-disabled') || '').trim().toLowerCase() !== 'true';
                    });
                    if (!el) return false;
                    el.scrollIntoView({ block: 'center', inline: 'center' });
                    for (const evt of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
                        el.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    }
                    el.click();
                    return true;
                }
                """,
                sel,
            ))
        except Exception:
            return False

    def _click_stepper_decrease(self, key: str) -> bool:
        sel = self.STEPPER_DECREASE_SELECTORS.get(key)
        if not sel:
            return False
        try:
            loc = self.page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=400):
                if loc.is_disabled():
                    return False
                loc.click(timeout=1200)
                return True
        except Exception:
            pass
        try:
            return bool(self.page.evaluate(
                """
                (selector) => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const nodes = [...document.querySelectorAll(selector)].filter(isVisible);
                    const el = nodes.find((n) => {
                        if (n.hasAttribute('disabled')) return false;
                        return (n.getAttribute('aria-disabled') || '').trim().toLowerCase() !== 'true';
                    });
                    if (!el) return false;
                    el.scrollIntoView({ block: 'center', inline: 'center' });
                    for (const evt of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
                        el.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                    }
                    el.click();
                    return true;
                }
                """,
                sel,
            ))
        except Exception:
            return False

    def _discover_available_stepper_keys(self) -> list:
        """
        Resolve visible/enabled guest steppers via stable data-testid attributes.
        This avoids brittle class-based checks and locator visibility races.
        """
        try:
            keys = self.page.evaluate(
                """
                () => {
                    const map = {
                        adults: 'button[data-testid="stepper-adults-increase-button"]',
                        children: 'button[data-testid="stepper-children-increase-button"]',
                        infants: 'button[data-testid="stepper-infants-increase-button"]',
                        pets: 'button[data-testid="stepper-pets-increase-button"]',
                    };
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const out = [];
                    for (const [key, selector] of Object.entries(map)) {
                        const nodes = [...document.querySelectorAll(selector)].filter(isVisible);
                        const enabled = nodes.some((el) => {
                            if (el.hasAttribute('disabled')) return false;
                            return (el.getAttribute('aria-disabled') || '').trim().toLowerCase() !== 'true';
                        });
                        if (enabled) out.push(key);
                    }
                    return out;
                }
                """
            )
            if isinstance(keys, list):
                return [str(k) for k in keys if k in self.STEPPER_INCREASE_SELECTORS]
        except Exception:
            pass
        return []

    def _read_stepper_values(self) -> dict:
        values = {"adults": 0, "children": 0, "infants": 0, "pets": 0}
        for key, sel in self.STEPPER_VALUE_SELECTORS.items():
            try:
                num = self.page.evaluate(
                    """
                    (selector) => {
                        const isVisible = (el) => {
                            if (!el) return false;
                            const r = el.getBoundingClientRect();
                            if (!r || r.width <= 0 || r.height <= 0) return false;
                            const s = window.getComputedStyle(el);
                            return s.display !== 'none' && s.visibility !== 'hidden';
                        };
                        const el = [...document.querySelectorAll(selector)].find(isVisible);
                        if (!el) return null;
                        const text = (el.textContent || '').trim();
                        const m = text.match(/\\d+/);
                        return m ? parseInt(m[0], 10) : null;
                    }
                    """,
                    sel,
                )
                if isinstance(num, int):
                    values[key] = num
            except Exception:
                continue
        return values

    def _close_guest_popup(self) -> None:
        if not self._popup_is_open():
            return
        for _ in range(3):
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                break
            time.sleep(0.3)
            if not self._popup_is_open():
                return

    def _get_guest_display(self) -> str:
        """Read the current guest count text from the guest field."""
        selectors = [
            '[role="button"][aria-expanded]:has-text("Who")',
            '[role="button"][aria-expanded]:has-text("guest")',
            'div[role="button"][aria-expanded][style*="grid-column: last"]',
            '[data-testid="structured-search-input-field-guests-button"]',
            '[data-testid*="structured-search-input-field-guests"]',
        ]
        for sel in selectors:
            try:
                el = self.page.query_selector(sel)
                if not el:
                    continue
                text = (el.inner_text() or "").strip()
                if text:
                    return text
                aria = (el.get_attribute("aria-label") or "").strip()
                if aria:
                    return aria
            except Exception:
                continue
        try:
            text = self.page.evaluate(
                """
                () => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const nodes = [...document.querySelectorAll(
                        '[role="button"][aria-expanded], [data-testid*="structured-search-input-field-guests"]'
                    )].filter((el) => {
                        if (!isVisible(el)) return false;
                        const t = (el.innerText || el.textContent || '').trim().toLowerCase();
                        return t.includes('who') || t.includes('guest');
                    });
                    for (const el of nodes) {
                        const t = (el.innerText || el.textContent || '').trim();
                        if (t && !t.toLowerCase().includes('wishlist')) return t;
                    }
                    return '';
                }
                """
            )
            return (text or "").strip()
        except Exception:
            pass
        return ""

    def _read_date_field_values(self) -> tuple[str, str]:
        checkin_text = ""
        checkout_text = ""
        checkin_selectors = [
            '[data-testid="structured-search-input-field-split-dates-0"]',
            '[data-testid*="structured-search-input-field-split-dates-0"]',
            '[data-testid*="structured-search-input-field-checkin"]',
            'button[aria-label*="check in" i]',
        ]
        checkout_selectors = [
            '[data-testid="structured-search-input-field-split-dates-1"]',
            '[data-testid*="structured-search-input-field-split-dates-1"]',
            '[data-testid*="structured-search-input-field-checkout"]',
            'button[aria-label*="check out" i]',
        ]

        for sel in checkin_selectors:
            try:
                el = self.page.query_selector(sel)
                if not el:
                    continue
                text = ((el.inner_text() or "").strip() or (el.get_attribute("aria-label") or "").strip())
                if text:
                    checkin_text = text
                    break
            except Exception:
                continue

        for sel in checkout_selectors:
            try:
                el = self.page.query_selector(sel)
                if not el:
                    continue
                text = ((el.inner_text() or "").strip() or (el.get_attribute("aria-label") or "").strip())
                if text:
                    checkout_text = text
                    break
            except Exception:
                continue

        return checkin_text, checkout_text

    @staticmethod
    def _is_real_date_value(value: str) -> bool:
        normalized = (value or "").strip().lower()
        blocked = {"", "add dates", "check in", "check out", "dates", "when"}
        return normalized not in blocked

    @classmethod
    def _month_token_number(cls, token: str) -> int | None:
        return cls.MONTH_TOKEN_TO_NUMBER.get((token or "").strip().lower())

    @classmethod
    def _parse_month_year_label(cls, value: str) -> tuple[int | None, int | None]:
        month_pattern = (
            r"january|february|march|april|may|june|july|august|"
            r"september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
        )
        match = re.search(rf"\b({month_pattern})\.?\s+(20\d{{2}})\b", value or "", re.IGNORECASE)
        if not match:
            return None, None
        month_num = cls._month_token_number(match.group(1))
        year_num = int(match.group(2))
        return year_num, month_num

    @classmethod
    def _parse_date_text(
        cls,
        value: str,
        fallback_year: int | None = None,
        fallback_month: int | None = None,
    ) -> date | None:
        text = " ".join((value or "").split())
        if not text:
            return None

        iso_match = re.search(r"\b(20\d{2})[-/]([01]?\d)[-/]([0-3]?\d)\b", text)
        if iso_match:
            try:
                return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            except ValueError:
                pass

        month_pattern = (
            r"january|february|march|april|may|june|july|august|"
            r"september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
        )
        month_first = re.search(
            rf"\b({month_pattern})\.?\s+([0-3]?\d)(?:st|nd|rd|th)?(?:,|\s)*(20\d{{2}})?\b",
            text,
            re.IGNORECASE,
        )
        if month_first:
            month_num = cls._month_token_number(month_first.group(1))
            day_num = int(month_first.group(2))
            year_num = int(month_first.group(3)) if month_first.group(3) else fallback_year
            if month_num and year_num:
                try:
                    return date(year_num, month_num, day_num)
                except ValueError:
                    pass

        day_first = re.search(
            rf"\b([0-3]?\d)(?:st|nd|rd|th)?\s+({month_pattern})\.?(?:,|\s)*(20\d{{2}})?\b",
            text,
            re.IGNORECASE,
        )
        if day_first:
            day_num = int(day_first.group(1))
            month_num = cls._month_token_number(day_first.group(2))
            year_num = int(day_first.group(3)) if day_first.group(3) else fallback_year
            if month_num and year_num:
                try:
                    return date(year_num, month_num, day_num)
                except ValueError:
                    pass

        if fallback_year and fallback_month:
            only_day = re.search(r"\b([0-3]?\d)\b", text)
            if only_day:
                try:
                    return date(fallback_year, fallback_month, int(only_day.group(1)))
                except ValueError:
                    pass

        return None

    def _range_is_logical(self, checkin_value: str, checkout_value: str) -> bool:
        fallback_year, fallback_month = self._parse_month_year_label(
            (self.shared_state.get("selected_month") or "").strip()
        )
        checkin_dt = self._parse_date_text(checkin_value, fallback_year=fallback_year, fallback_month=fallback_month)
        checkout_dt = self._parse_date_text(checkout_value, fallback_year=fallback_year, fallback_month=fallback_month)
        if checkin_dt and checkout_dt:
            return checkout_dt > checkin_dt
        return True

    def _read_selected_dates_from_calendar(self) -> tuple[str, str]:
        try:
            payload = self.page.evaluate(
                """
                () => {
                    const q = [
                        'button[data-state--date-string][aria-label]',
                        '[data-state--date-string][aria-label]',
                        '[data-testid*="calendar-day"][aria-label]',
                        'div[role="dialog"] button[aria-label]',
                        'table button[aria-label]',
                    ].join(', ');

                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    };

                    let checkin = '';
                    let checkout = '';
                    for (const el of document.querySelectorAll(q)) {
                        if (!isVisible(el)) continue;
                        const label = (el.getAttribute('aria-label') || '').trim();
                        if (!label) continue;
                        const norm = label.toLowerCase();
                        if (!checkin && /selected\\s*check-?in\\s*date/.test(norm)) {
                            checkin = label;
                            continue;
                        }
                        if (!checkout && /selected\\s*check-?out\\s*date/.test(norm)) {
                            checkout = label;
                            continue;
                        }
                    }
                    return { checkin, checkout };
                }
                """
            )
            if isinstance(payload, dict):
                return (payload.get("checkin") or "").strip(), (payload.get("checkout") or "").strip()
        except Exception:
            pass
        return "", ""

    def _calendar_has_selected_range(self) -> bool:
        checkin, checkout = self._read_selected_dates_from_calendar()
        return (
            self._is_real_date_value(checkin)
            and self._is_real_date_value(checkout)
            and self._range_is_logical(checkin, checkout)
        )

    def _saved_dates_are_logical(self) -> bool:
        saved_checkin = (self.shared_state.get("checkin_date") or "").strip()
        saved_checkout = (self.shared_state.get("checkout_date") or "").strip()
        return (
            self._is_real_date_value(saved_checkin)
            and self._is_real_date_value(saved_checkout)
            and self._range_is_logical(saved_checkin, saved_checkout)
        )

    def _ui_shows_saved_day_range(self) -> bool:
        checkin_saved = (self.shared_state.get("checkin_date") or "").strip()
        checkout_saved = (self.shared_state.get("checkout_date") or "").strip()
        if not (checkin_saved and checkout_saved):
            return False

        checkin_tokens = self._extract_date_tokens(checkin_saved)
        checkout_tokens = self._extract_date_tokens(checkout_saved)
        checkin_day = (checkin_tokens.get("day") or "").strip()
        checkout_day = (self._extract_date_tokens(checkout_saved).get("day") or "").strip()
        month_hint = (checkin_tokens.get("month") or checkout_tokens.get("month") or "").strip().lower()
        if not (checkin_day and checkout_day):
            return False

        try:
            merged = self.page.evaluate(
                """
                () => {
                    const selectors = [
                        '[data-testid="structured-search-input-field-split-dates"]',
                        '[data-testid*="structured-search-input-field-split-dates"]',
                        '[data-testid="structured-search-input-field-dates-button"]',
                        '[data-testid*="structured-search-input-field-dates"]',
                        'button[aria-label*="check in" i]',
                        'button[aria-label*="check out" i]',
                        'button[aria-label*="dates" i]',
                        'button[aria-label*="when" i]',
                        '[role="button"]:has-text("When")',
                        '[role="button"][aria-expanded]',
                        'div[role="button"][aria-expanded][style*="grid-column: center"]',
                    ];
                    const out = [];
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    for (const sel of selectors) {
                        for (const el of document.querySelectorAll(sel)) {
                            if (!isVisible(el)) continue;
                            const txt = (
                                (el.innerText || el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '')
                            ).replace(/\\s+/g, ' ').trim();
                            if (txt) out.push(txt.toLowerCase());
                        }
                    }
                    return out.join(' | ');
                }
                """
            ) or ""
        except Exception:
            return False

        has_checkin = bool(re.search(rf"\b0?{re.escape(checkin_day)}\b", merged))
        has_checkout = bool(re.search(rf"\b0?{re.escape(checkout_day)}\b", merged))
        if not (has_checkin and has_checkout):
            return False
        if month_hint:
            short_month = month_hint[:3]
            if month_hint not in merged and short_month not in merged:
                return False
        return True

    def _dates_present_in_ui(self) -> bool:
        checkin_text, checkout_text = self._read_date_field_values()
        if (
            self._is_real_date_value(checkin_text)
            and self._is_real_date_value(checkout_text)
            and self._range_is_logical(checkin_text, checkout_text)
        ):
            return True

        if self._calendar_has_selected_range():
            return True

        # Final fallback: if Step 03 already persisted logical values, accept them.
        return self._saved_dates_are_logical()

    def _dates_present_in_ui_strict(self) -> bool:
        """
        Strict UI check: only return True if dates are actually present/selected in the UI,
        not just in checkpoint/shared state.
        """
        checkin_text, checkout_text = self._read_date_field_values()
        if (
            self._is_real_date_value(checkin_text)
            and self._is_real_date_value(checkout_text)
            and self._range_is_logical(checkin_text, checkout_text)
        ):
            return True
        if self._ui_shows_saved_day_range():
            return True
        return self._calendar_has_selected_range()

    def _open_date_picker(self) -> bool:
        if self._picker_is_open():
            return True

        # In compact mode, expand the search bar and close guest panel first.
        self._close_guest_popup()
        self._expand_compact_search_bar()
        time.sleep(0.2)

        for sel in self.DATE_FIELD_SELECTORS:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    try:
                        loc.scroll_into_view_if_needed(timeout=800)
                    except Exception:
                        pass
                    loc.click(timeout=1200)
                    time.sleep(0.8)
                    if self._picker_is_open():
                        return True
            except Exception:
                continue
        try:
            clicked = bool(self.page.evaluate("""
                () => {
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const s = window.getComputedStyle(el);
                        return s.display !== 'none' && s.visibility !== 'hidden';
                    };
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const clickTarget = (node) => {
                        let cur = node;
                        for (let i = 0; i < 8 && cur; i += 1) {
                            const role = norm(cur.getAttribute('role'));
                            if (
                                cur.tagName === 'BUTTON' ||
                                role === 'button' ||
                                cur.matches?.('[data-testid*="dates"], [data-testid*="split-dates"]')
                            ) {
                                for (const evt of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
                                    cur.dispatchEvent(new MouseEvent(evt, { bubbles: true, cancelable: true, view: window }));
                                }
                                cur.click();
                                return true;
                            }
                            cur = cur.parentElement;
                        }
                        return false;
                    };

                    const candidates = [...document.querySelectorAll('button, div, span, [role="button"]')].filter(isVisible);
                    const target = candidates.find((e) => {
                        const text = norm(e.innerText || e.textContent);
                        const aria = norm(e.getAttribute('aria-label'));
                        return (
                            text.includes('when') ||
                            text.includes('add dates') ||
                            aria.includes('check in') ||
                            aria.includes('check out') ||
                            aria.includes('dates')
                        );
                    });
                    if (!target) return false;
                    return clickTarget(target);
                }
            """))
            if clicked:
                time.sleep(0.8)
                if self._picker_is_open():
                    return True
            return False
        except Exception:
            return False

    def _picker_is_open(self) -> bool:
        try:
            return bool(self.page.evaluate("""
                () => {
                    const nextBtns = [...document.querySelectorAll(
                        'button[aria-label*="Move forward" i], button[aria-label*="next month" i], button[data-testid*="calendar-next"]'
                    )].filter(el => el.offsetParent !== null);
                    const dayBtns = [...document.querySelectorAll(
                        'button[data-state--date-string], [data-state--date-string], [data-testid*="calendar-day"], div[role="dialog"] button[aria-label], table button[aria-label]'
                    )].filter(el => {
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        if (el.hasAttribute('disabled')) return false;
                        if ((el.getAttribute('aria-disabled') || '').toLowerCase() === 'true') return false;
                        return true;
                    });
                    return nextBtns.length > 0 || dayBtns.length >= 8;
                }
            """))
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
        month_text = month_match.group(1) if month_match else ""
        day_text = day_match.group(1).lstrip("0") if day_match else ""
        year_text = year_match.group(1) if year_match else ""
        month_num = Step04GuestPicker._month_token_number(month_text) if month_text else None
        state_date = ""
        if month_num and day_text and year_text:
            state_date = f"{year_text}-{month_num:02d}-{int(day_text):02d}"
        return {
            "raw": date_label or "",
            "month": month_text,
            "day": day_text,
            "year": year_text,
            "state_date": state_date,
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
                    const stateDate = norm(payload.state_date);

                    const buttons = [...document.querySelectorAll(
                        '[data-testid="datepicker-portal"] [data-state--date-string][aria-label], [data-testid="datepicker-portal"] button[aria-label], div[role="dialog"] [data-state--date-string][aria-label], div[role="dialog"] button[aria-label], table [data-state--date-string][aria-label], table button[aria-label]'
                    )].filter(el => {
                        if (el.offsetParent === null) return false;
                        if (el.hasAttribute('disabled')) return false;
                        const ariaDisabled = (el.getAttribute('aria-disabled') || '').trim().toLowerCase();
                        if (ariaDisabled === 'true') return false;
                        const aria = norm(el.getAttribute('aria-label'));
                        if (aria.includes('next month') || aria.includes('previous month') || aria.includes('move forward') || aria.includes('move backward')) {
                            return false;
                        }
                        return true;
                    });

                    let target = null;

                    if (raw) {
                        target = buttons.find(b => norm(b.getAttribute('aria-label')) === raw);
                    }
                    if (!target && stateDate) {
                        target = buttons.find(b => norm(b.getAttribute('data-state--date-string')) === stateDate);
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

    def _restore_dates_if_needed(self, force_apply: bool = False) -> bool:
        if force_apply and self._dates_present_in_ui_strict():
            print("  Dates already visible in UI after screenshot.")
            return True

        if not force_apply and self._dates_present_in_ui():
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
                if not force_apply and self._dates_present_in_ui():
                    return True
        if not (checkin_saved and checkout_saved):
            return False

        if force_apply:
            print("  Re-applying dates after screenshot from checkpoint.")
        else:
            print("  Dates missing — restoring from checkpoint.")
        if not self._open_date_picker():
            self._expand_compact_search_bar()
            self._close_guest_popup()
            time.sleep(0.3)
            if not self._open_date_picker():
                print("  Date picker could not be reopened during date restore.")
                # Do not hard-fail when UI is compact; keep saved dates for URL/search fallback.
                return self._dates_present_in_ui_strict() or self._saved_dates_are_logical()

        self._ensure_dates_tab_selected()
        self._move_to_saved_month()
        self._ensure_dates_tab_selected()
        if not force_apply and self._calendar_has_selected_range():
            return True

        if not self._click_saved_date(checkin_saved):
            print("  Failed to click saved check-in date during restore.")
            return self._dates_present_in_ui_strict()
        time.sleep(0.5)

        if not self._click_saved_date(checkout_saved):
            print("  Failed to click saved check-out date during restore.")
            return self._dates_present_in_ui_strict() or self._calendar_has_selected_range()
        time.sleep(0.8)

        restored_ok = self._dates_present_in_ui_strict() or self._calendar_has_selected_range()
        print(f"  Date restore verification after reapply: {restored_ok}")
        return restored_ok

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

    def _restore_guests_if_needed(self, target_counts: dict | None) -> bool:
        normalized_target = {"adults": 0, "children": 0, "infants": 0, "pets": 0}
        for key in normalized_target:
            try:
                normalized_target[key] = max(0, int((target_counts or {}).get(key, 0)))
            except Exception:
                normalized_target[key] = 0

        target_total = sum(normalized_target.values())
        if target_total <= 0:
            return True

        # Fast path: if guest summary already matches expected in compact UI, don't reopen popup.
        guest_display = (self._get_guest_display() or "").strip().lower()
        displayed_guest_count = self._extract_first_int(guest_display) or 0
        expected_guest_count = normalized_target["adults"] + normalized_target["children"]
        extras_ok = True
        if normalized_target["infants"] > 0 and "infant" not in guest_display:
            extras_ok = False
        if normalized_target["pets"] > 0 and "pet" not in guest_display:
            extras_ok = False
        if displayed_guest_count == expected_guest_count and extras_ok:
            self.shared_state["guest_breakdown"] = dict(normalized_target)
            self.shared_state["guest_total_added"] = target_total
            self.shared_state["guest_count"] = expected_guest_count
            return True

        if not self._open_guest_field():
            self._expand_compact_search_bar()
            if not self._open_guest_field():
                # Keep saved guest state if popup cannot be reopened after screenshot.
                self.shared_state["guest_breakdown"] = dict(normalized_target)
                self.shared_state["guest_total_added"] = target_total
                self.shared_state["guest_count"] = expected_guest_count
                return expected_guest_count > 0

        popup_open = False
        for _ in range(5):
            if self._popup_is_open():
                popup_open = True
                break
            self._open_guest_field()
            time.sleep(0.3)
        if not popup_open:
            self.shared_state["guest_breakdown"] = dict(normalized_target)
            self.shared_state["guest_total_added"] = target_total
            self.shared_state["guest_count"] = expected_guest_count
            return expected_guest_count > 0

        current = self._read_stepper_values()
        for key in ["adults", "children", "infants", "pets"]:
            desired = normalized_target[key]
            guard = 0
            while current.get(key, 0) < desired and guard < 24:
                guard += 1
                if not self._click_stepper_increase(key):
                    break
                time.sleep(0.2)
                current = self._read_stepper_values()

            while current.get(key, 0) > desired and guard < 48:
                guard += 1
                if not self._click_stepper_decrease(key):
                    break
                time.sleep(0.2)
                current = self._read_stepper_values()

        final_values = self._read_stepper_values()
        guests_ok = all(final_values.get(k, 0) == normalized_target[k] for k in normalized_target)

        if not guests_ok:
            # Compact header fallback: validate via summary text when stepper panel
            # re-renders before values can be read back.
            self._close_guest_popup()
            time.sleep(0.35)
            guest_display = (self._get_guest_display() or "").strip().lower()
            displayed_guest_count = self._extract_first_int(guest_display) or 0
            extras_ok = True
            if normalized_target["infants"] > 0 and "infant" not in guest_display:
                extras_ok = False
            if normalized_target["pets"] > 0 and "pet" not in guest_display:
                extras_ok = False
            if displayed_guest_count == expected_guest_count and extras_ok:
                final_values = dict(normalized_target)
                guests_ok = True

        self.shared_state["guest_breakdown"] = final_values
        self.shared_state["guest_total_added"] = sum(final_values.values())
        self.shared_state["guest_count"] = final_values.get("adults", 0) + final_values.get("children", 0)
        self.checkpoint("step04_guests_rehydrated")

        self._close_guest_popup()
        time.sleep(0.5)
        return guests_ok

    def _rehydrate_context_before_search(self, target_guest_counts: dict) -> tuple[bool, bool, bool]:
        self.restore_checkpoint()
        self.safe_dismiss_popups()
        if not (
            (self.shared_state.get("selected_location") or "").strip()
            and (self.shared_state.get("checkin_date") or "").strip()
            and (self.shared_state.get("checkout_date") or "").strip()
        ):
            if self._restore_context_from_db():
                self.checkpoint("step04_context_restored_from_db")

        location_ready = self._restore_location_if_needed()
        dates_ready = self._restore_dates_if_needed(force_apply=True)
        guests_ready = self._restore_guests_if_needed(target_guest_counts)
        self.checkpoint("step04_context_rehydrated_pre_search")
        return location_ready, dates_ready, guests_ready

    def run(self) -> ResultModel:
        print("\n[Step 04] Guest Picker Interaction...")
        time.sleep(1)
        self.restore_checkpoint()
        self.safe_dismiss_popups()
        if not (
            (self.shared_state.get("selected_location") or "").strip()
            and (self.shared_state.get("checkin_date") or "").strip()
            and (self.shared_state.get("checkout_date") or "").strip()
        ):
            if self._restore_context_from_db():
                print("  Context restored from DB before Step 04 interactions.")
                self.checkpoint("step04_context_restored_from_db")
        if not self.shared_state.get("selected_location"):
            self.shared_state["selected_location"] = (
                self.shared_state.get("chosen_suggestion")
                or self.shared_state.get("selected_country")
                or ""
            )

        location_ready = self._restore_location_if_needed()
        dates_ready = self._restore_dates_if_needed()
        print(f"  Search context ready for Step 04: {location_ready and dates_ready}")
        if not (location_ready and dates_ready):
            return self.save(
                False,
                "Step 04 requires location + dates in the search bar, but context restore failed.",
                "",
                selected_location=(self.shared_state.get("selected_location") or ""),
                selected_month=(self.shared_state.get("selected_month") or ""),
                checkin_date=(self.shared_state.get("checkin_date") or ""),
                checkout_date=(self.shared_state.get("checkout_date") or ""),
            )
        self.checkpoint("step04_dates_verified")

        # Click the guest input field
        guest_click_ok = self._open_guest_field()
        time.sleep(1.5)

        # Wait for the popup to open
        popup_visible = False
        for attempt in range(8):
            if self._popup_is_open():
                popup_visible = True
                break
            if self._guest_trigger_expanded():
                time.sleep(0.35)
                if self._popup_is_open():
                    popup_visible = True
                    break
            # Retry field click because Airbnb can collapse/re-render the search controls.
            if attempt < 7:
                self._open_guest_field()
            print(f"  Waiting for guest popup... attempt {attempt + 1}")
            time.sleep(1)

        if not popup_visible:
            return self.save(
                False,
                f"Guest picker popup did not open. Initial guest click success: {guest_click_ok}.",
                "",
                selected_location=(self.shared_state.get("selected_location") or ""),
                selected_month=(self.shared_state.get("selected_month") or ""),
                checkin_date=(self.shared_state.get("checkin_date") or ""),
                checkout_date=(self.shared_state.get("checkout_date") or ""),
            )

        # Randomly select 2-5 guests distributed across categories
        total_to_add = random.randint(2, 5)
        added_counts = {"adults": 0, "children": 0, "infants": 0, "pets": 0}
        available_keys = self._discover_available_stepper_keys()

        print(f"  Increase controls available: {available_keys}, Target selections: {total_to_add}")
        if not available_keys:
            return self.save(
                False,
                "Guest popup opened, but no stepper increase controls were visible.",
                "",
                selected_location=(self.shared_state.get("selected_location") or ""),
                selected_month=(self.shared_state.get("selected_month") or ""),
                checkin_date=(self.shared_state.get("checkin_date") or ""),
                checkout_date=(self.shared_state.get("checkout_date") or ""),
            )

        remaining = total_to_add
        # Airbnb generally expects at least one adult for a valid guest search.
        if "adults" in available_keys and remaining > 0:
            if self._click_stepper_increase("adults"):
                added_counts["adults"] += 1
                remaining -= 1
                time.sleep(0.35)

        guard = 0
        pool = list(available_keys)
        while remaining > 0 and pool and guard < 20:
            guard += 1
            key = random.choice(pool)
            if self._click_stepper_increase(key):
                added_counts[key] += 1
                remaining -= 1
                time.sleep(0.3)
                continue
            # remove non-clickable controls to avoid looping forever
            pool = [k for k in pool if k != key]

        stepper_values = self._read_stepper_values()
        if any(v > 0 for v in stepper_values.values()):
            added_counts = stepper_values
        total_added = sum(added_counts.values())

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

        # Collapse popup so the guest field text in the search bar is readable.
        self._close_guest_popup()
        time.sleep(0.8)

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
                loc = self.page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=500):
                    loc.click(timeout=1200)
                    search_clicked = True
                    print(f"  Search button clicked via: {sel}")
                    break
            except Exception:
                continue

        if not search_clicked:
            # JS fallback
            try:
                search_clicked = bool(self.page.evaluate("""
                    () => {
                        const isVisible = (el) => {
                            if (!el) return false;
                            const r = el.getBoundingClientRect();
                            if (!r || r.width <= 0 || r.height <= 0) return false;
                            const s = window.getComputedStyle(el);
                            return s.display !== 'none' && s.visibility !== 'hidden';
                        };
                        const clickChain = (el) => {
                            let cur = el;
                            for (let i = 0; i < 8 && cur; i += 1) {
                                const role = (cur.getAttribute('role') || '').toLowerCase();
                                if (
                                    cur.tagName === 'BUTTON' ||
                                    role === 'button' ||
                                    (cur.getAttribute('data-testid') || '').includes('search-button')
                                ) {
                                    cur.click();
                                    return true;
                                }
                                cur = cur.parentElement;
                            }
                            return false;
                        };

                        const candidates = [
                            ...document.querySelectorAll('[data-testid="structured-search-input-search-button"]'),
                            ...document.querySelectorAll('button, [role="button"], div, span'),
                        ].filter(isVisible);

                        for (const el of candidates) {
                            const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                            if (text === 'search' || text.includes('\nsearch') || text.startsWith('search')) {
                                if (clickChain(el)) return true;
                            }
                        }
                        return false;
                    }
                """))
                if search_clicked:
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
        return self.save(
            passed,
            comment,
            "",
            selected_location=(self.shared_state.get("selected_location") or ""),
            selected_month=(self.shared_state.get("selected_month") or ""),
            checkin_date=(self.shared_state.get("checkin_date") or ""),
            checkout_date=(self.shared_state.get("checkout_date") or ""),
        )
