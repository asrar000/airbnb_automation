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
import re
import time
from datetime import date

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

    DAY_CELL_SELECTORS = [
        'button[data-state--date-string]',
        '[role="button"][data-state--date-string]',
        '[data-state--date-string]',
        '[data-testid="datepicker-portal"] button[aria-label]',
        '[data-testid="datepicker-portal"] [role="button"][aria-label]',
        '[data-testid="datepicker-portal"] [data-testid*="calendar-day"]',
        '[data-testid="datepicker-portal"] [role="gridcell"]',
        '[data-testid="datepicker-portal"] td[aria-label]',
        '[data-testid="structured-search-input-field-dates-panel"] button',
        '[data-testid="structured-search-input-field-dates-panel"] [role="button"]',
        '[data-testid="structured-search-input-field-dates-panel"] [role="gridcell"]',
        '[data-testid="structured-search-input-field-dates-panel"] td',
        'div[role="dialog"] button[aria-label]',
        'div[role="dialog"] [role="button"][aria-label]',
        'div[role="dialog"] [data-testid*="calendar-day"]',
        'div[role="dialog"] [role="gridcell"]',
        'div[role="dialog"] td[aria-label]',
        'table button[aria-label]',
        'table td[aria-label]',
        'table button',
        'table td',
    ]

    CHECKIN_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-split-dates-0"]',
        '[data-testid*="structured-search-input-field-split-dates-0"]',
        '[data-testid*="structured-search-input-field-checkin"]',
    ]

    CHECKOUT_FIELD_SELECTORS = [
        '[data-testid="structured-search-input-field-split-dates-1"]',
        '[data-testid*="structured-search-input-field-split-dates-1"]',
        '[data-testid*="structured-search-input-field-checkout"]',
    ]

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

    def _picker_is_open(self, timeout_ms: int = 3000) -> bool:
        """Check if the calendar date picker is currently visible."""
        try:
            picker_open = bool(self.page.evaluate("""
                () => {
                    const nextBtns = [...document.querySelectorAll(
                        'button[aria-label*="Move forward" i], button[aria-label*="next month" i], button[data-testid*="calendar-next"]'
                    )].filter(el => el.offsetParent !== null);

                    const dayBtns = [...document.querySelectorAll(
                        'button[data-state--date-string], [role="button"][data-state--date-string], [data-state--date-string], [data-testid="datepicker-portal"] button[aria-label], [data-testid="datepicker-portal"] td[aria-label], [data-testid="datepicker-portal"] [data-testid*="calendar-day"], div[role="dialog"] button[aria-label], div[role="dialog"] td[aria-label], div[role="dialog"] [data-testid*="calendar-day"], table button[aria-label], table td[aria-label]'
                    )].filter(el => {
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        if (el.hasAttribute('disabled')) return false;
                        if ((el.getAttribute('aria-disabled') || '').toLowerCase() === 'true') return false;
                        const label = (el.getAttribute('aria-label') || '').trim();
                        const text = (el.innerText || el.textContent || '').trim();
                        const stateDate = (el.getAttribute('data-state--date-string') || '').trim();
                        return Boolean(stateDate) || label.length > 4 || /\\b([0-3]?\\d)\\b/.test(text);
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

    def _ensure_dates_tab_selected(self) -> bool:
        """
        Airbnb can remember previous picker mode (Months/Flexible).
        Force the 'Dates' tab before trying to click day cells.
        """
        try:
            ensured = bool(self.page.evaluate("""
                () => {
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    };

                    const isActive = (el) => {
                        const ariaSelected = norm(el.getAttribute('aria-selected')) === 'true';
                        const ariaPressed = norm(el.getAttribute('aria-pressed')) === 'true';
                        const cls = norm((el.className || '').toString());
                        return ariaSelected || ariaPressed || cls.includes('selected') || cls.includes('active');
                    };

                    const tabs = [...document.querySelectorAll(
                        'button, [role="tab"], div[role="tab"], span[role="tab"]'
                    )].filter((el) => {
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

    def _get_day_buttons(self) -> list[dict]:
        """
        Return all visible + enabled day candidates in DOM order.
        Includes button and table-cell based calendar implementations.
        """
        try:
            result = self.page.evaluate(
                """
                (payload) => {
                    const selectors = payload.selectors || [];
                    const seen = new Set();
                    const seenByPosition = new Set();
                    const nodes = [];
                    const roots = [
                        ...document.querySelectorAll(
                            '[data-testid="datepicker-portal"], [data-testid="structured-search-input-field-dates-panel"], div[role="dialog"], [data-testid*="calendar"]'
                        )
                    ];

                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        if (style.display === 'none' || style.visibility === 'hidden') return false;
                        return true;
                    };

                    const isEnabled = (el) => {
                        if (!el) return false;
                        const checks = [
                            el,
                            el.closest('button, [role="button"], td, [role="gridcell"]'),
                            el.parentElement,
                        ].filter(Boolean);
                        for (const node of checks) {
                            if (node.hasAttribute('disabled')) return false;
                            const ariaDisabled = (node.getAttribute('aria-disabled') || '').trim().toLowerCase();
                            if (ariaDisabled === 'true') return false;
                            if ((node.getAttribute('data-is-day-blocked') || '').toLowerCase() === 'true') return false;
                            if ((node.getAttribute('data-disabled') || '').toLowerCase() === 'true') return false;
                            if ((node.getAttribute('data-unavailable') || '').toLowerCase() === 'true') return false;
                        }
                        return true;
                    };

                    const readText = (el) =>
                        ((el?.innerText || el?.textContent || '').replace(/\\s+/g, ' ')).trim();

                    for (const sel of selectors) {
                        for (const el of document.querySelectorAll(sel)) {
                            if (seen.has(el)) continue;
                            seen.add(el);
                            nodes.push(el);
                        }
                    }

                    // Calendar variants sometimes render day cells only under month roots
                    // without stable test IDs; add a scoped fallback scan.
                    const fallbackScopedSelectors = [
                        '[data-state--date-string]',
                        'button[data-state--date-string]',
                        'button',
                        '[role="button"]',
                        '[role="gridcell"]',
                        'td',
                        '[data-testid*="calendar-day"]',
                    ];
                    for (const root of roots) {
                        if (!isVisible(root)) continue;
                        for (const sel of fallbackScopedSelectors) {
                            for (const el of root.querySelectorAll(sel)) {
                                if (seen.has(el)) continue;
                                seen.add(el);
                                nodes.push(el);
                            }
                        }
                    }

                    const out = [];
                    nodes.forEach((el, domIndex) => {
                        const clickable = el.matches('button, [role="button"]')
                            ? el
                            : el.querySelector('button, [role="button"]');
                        const target = clickable || el;
                        if (!isVisible(target) || !isEnabled(target)) return;

                        const r = target.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return;

                        const label = (target.getAttribute('aria-label') || el.getAttribute('aria-label') || '').trim();
                        const text = readText(target) || readText(el);
                        const testid = (target.getAttribute('data-testid') || el.getAttribute('data-testid') || '').trim();
                        const dataDate = (target.getAttribute('data-date') || el.getAttribute('data-date') || '').trim();
                        const stateDate = (target.getAttribute('data-state--date-string') || el.getAttribute('data-state--date-string') || '').trim();
                        const title = (target.getAttribute('title') || el.getAttribute('title') || '').trim();
                        const elId = (target.id || el.id || '').trim();

                        const attrBlob = `${label} ${testid} ${dataDate} ${stateDate} ${title} ${elId}`;
                        const hasStateDate = /^20\\d{2}-[01]\\d-[0-3]\\d$/.test(stateDate);
                        const hasDateishAttr =
                            /\\b(20\\d{2})[-/.]([01]?\\d)[-/.]([0-3]?\\d)\\b/.test(attrBlob) ||
                            /\\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\\b/i.test(attrBlob) ||
                            /calendar-day/i.test(testid);
                        const dayToken = text.match(/\\b([1-9]|[12]\\d|3[01])\\b/);
                        const hasDateActionWord =
                            /\\b(available|check-?in|check\\s*out|checkout|selected|today)\\b/i.test(label);

                        const inDateGrid = Boolean(
                            target.closest('table, [role="grid"], [role="row"], [role="gridcell"], [data-testid*="calendar"], [data-testid*="month"]')
                        );
                        if (!inDateGrid && !/calendar-day/i.test(testid) && !hasStateDate && !hasDateActionWord) return;
                        if (!(dayToken || hasDateishAttr || hasStateDate)) return;

                        const x = r.left + r.width / 2;
                        const y = r.top + r.height / 2;
                        if (x < 0 || y < 0 || x > window.innerWidth || y > window.innerHeight) return;

                        const posKey = `${Math.round(x)}:${Math.round(y)}`;
                        if (seenByPosition.has(posKey)) return;
                        seenByPosition.add(posKey);

                        out.push({
                            dom_index: domIndex,
                            label,
                            text,
                            testid,
                            data_date: dataDate,
                            state_date: stateDate,
                            title,
                            el_id: elId,
                            x,
                            y,
                        });
                    });

                    return out;
                }
                """,
                {"selectors": self.DAY_CELL_SELECTORS},
            )
            if isinstance(result, list):
                return result
        except Exception:
            pass
        return []

    @classmethod
    def _month_token_number(cls, token: str) -> int | None:
        return cls.MONTH_TOKEN_TO_NUMBER.get((token or "").strip().lower())

    def _select_dates_with_bruteforce_click(self) -> tuple[str, str, bool]:
        """
        Last-resort click strategy when the structured day candidate parser returns 0.
        Returns (checkin_label, checkout_label, success).
        """
        try:
            payload = self.page.evaluate(
                """
                () => {
                    const seen = new Set();
                    const out = [];
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    };
                    const isEnabled = (el) => {
                        if (!el) return false;
                        if (el.hasAttribute('disabled')) return false;
                        const ariaDisabled = (el.getAttribute('aria-disabled') || '').trim().toLowerCase();
                        return ariaDisabled !== 'true';
                    };
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const readText = (el) =>
                        ((el?.innerText || el?.textContent || '').replace(/\\s+/g, ' ')).trim();

                    const roots = [
                        ...document.querySelectorAll(
                            '[data-testid="datepicker-portal"], [data-testid="structured-search-input-field-dates-panel"], div[role="dialog"], [data-testid*="calendar"]'
                        ),
                    ].filter(isVisible);
                    const scanRoots = roots.length ? roots : [document];

                    for (const root of scanRoots) {
                        for (const el of root.querySelectorAll('[data-state--date-string], button, [role="button"], [role="gridcell"], td')) {
                            if (!isVisible(el) || !isEnabled(el)) continue;
                            const target = el.matches('button, [role="button"]')
                                ? el
                                : el.querySelector('button, [role="button"]') || el;
                            if (!isVisible(target) || !isEnabled(target)) continue;

                            const aria = norm(target.getAttribute('aria-label') || el.getAttribute('aria-label'));
                            if (aria.includes('next month') || aria.includes('previous month') || aria.includes('move forward') || aria.includes('move backward')) {
                                continue;
                            }

                            const testid = norm(target.getAttribute('data-testid') || el.getAttribute('data-testid'));
                            const stateDate = norm(target.getAttribute('data-state--date-string') || el.getAttribute('data-state--date-string'));
                            const hasStateDate = /^20\\d{2}-[01]\\d-[0-3]\\d$/.test(stateDate);
                            const text = readText(target) || readText(el);
                            const dayToken = text.match(/\\b([1-9]|[12]\\d|3[01])\\b/);
                            const inGrid = Boolean(target.closest('table, [role="grid"], [role="row"], [role="gridcell"], [data-testid*="calendar"], [data-testid*="month"]'));
                            const hasDateWord = /\\b(available|check-?in|check\\s*out|checkout|selected|today)\\b/.test(aria);
                            if (!inGrid && !/calendar-day/.test(testid) && !hasStateDate && !hasDateWord) continue;
                            if (!dayToken && !/calendar-day/.test(testid) && !/(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)/.test(aria) && !hasStateDate) {
                                continue;
                            }

                            const r = target.getBoundingClientRect();
                            const x = r.left + r.width / 2;
                            const y = r.top + r.height / 2;
                            if (x < 0 || y < 0 || x > window.innerWidth || y > window.innerHeight) continue;
                            const key = `${Math.round(x)}:${Math.round(y)}`;
                            if (seen.has(key)) continue;
                            seen.add(key);
                            out.push({
                                x,
                                y,
                                label: target.getAttribute('aria-label') || '',
                                text,
                                state_date: stateDate,
                            });
                        }
                    }

                    if (out.length < 2) {
                        return { ok: false, count: out.length };
                    }
                    const parseStamp = (item) => {
                        const iso = norm(item.state_date);
                        if (/^20\\d{2}-[01]\\d-[0-3]\\d$/.test(iso)) {
                            return Date.parse(`${iso}T00:00:00Z`);
                        }
                        const lbl = norm(item.label);
                        const m = lbl.match(/\\b(20\\d{2})[-/]([01]?\\d)[-/]([0-3]?\\d)\\b/);
                        if (m) {
                            const mm = String(Number(m[2])).padStart(2, '0');
                            const dd = String(Number(m[3])).padStart(2, '0');
                            return Date.parse(`${m[1]}-${mm}-${dd}T00:00:00Z`);
                        }
                        return Number.NaN;
                    };

                    const withStamp = out
                        .map((item) => ({ item, stamp: parseStamp(item) }))
                        .filter((row) => !Number.isNaN(row.stamp))
                        .sort((a, b) => a.stamp - b.stamp);

                    const ordered = withStamp.length >= 2 ? withStamp.map((row) => row.item) : out;
                    const checkinIdx = Math.min(Math.max(1, Math.floor(ordered.length / 4)), ordered.length - 2);
                    let checkoutIdx = Math.min(checkinIdx + 3, ordered.length - 1);
                    if (checkoutIdx <= checkinIdx) checkoutIdx = Math.min(checkinIdx + 1, ordered.length - 1);
                    return {
                        ok: true,
                        count: ordered.length,
                        checkin: ordered[checkinIdx],
                        checkout: ordered[checkoutIdx],
                    };
                }
                """
            )
            if not isinstance(payload, dict) or not payload.get("ok"):
                return "", "", False

            checkin = payload.get("checkin") or {}
            checkout = payload.get("checkout") or {}
            self.page.mouse.click(float(checkin.get("x")), float(checkin.get("y")))
            time.sleep(0.8)
            self._ensure_picker_open(attempts=2)
            self._ensure_dates_tab_selected()
            self.page.mouse.click(float(checkout.get("x")), float(checkout.get("y")))
            time.sleep(0.8)
            checkin_label = (checkin.get("label") or checkin.get("text") or "").strip()
            checkout_label = (checkout.get("label") or checkout.get("text") or "").strip()
            return checkin_label, checkout_label, True
        except Exception:
            return "", "", False

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

    def _day_candidate_to_date(
        self,
        day: dict,
        fallback_year: int | None = None,
        fallback_month: int | None = None,
    ) -> date | None:
        for key in ("state_date", "label", "data_date", "testid", "title", "el_id", "text"):
            parsed = self._parse_date_text(
                day.get(key, ""),
                fallback_year=fallback_year,
                fallback_month=fallback_month,
            )
            if parsed:
                return parsed
        return None

    def _choose_day_pair(self, days: list[dict], month_label: str) -> tuple[dict | None, dict | None, bool]:
        """
        Choose check-in/check-out candidates.
        Returns (checkin_candidate, checkout_candidate, has_logical_range).
        """
        if len(days) < 2:
            return None, None, False

        fallback_year, fallback_month = self._parse_month_year_label(month_label)
        parsed_rows: list[tuple[date, dict]] = []
        for day in days:
            parsed = self._day_candidate_to_date(day, fallback_year=fallback_year, fallback_month=fallback_month)
            if parsed:
                parsed_rows.append((parsed, day))

        # Prefer date-based selection when dates are parsable.
        if len(parsed_rows) >= 2:
            unique_by_date: dict[date, dict] = {}
            for parsed, day in parsed_rows:
                unique_by_date.setdefault(parsed, day)
            ordered = sorted(unique_by_date.items(), key=lambda item: item[0])
            today = date.today()
            ordered = [row for row in ordered if row[0] >= today] or ordered
            if len(ordered) >= 2:
                checkin_pos = min(max(1, len(ordered) // 4), len(ordered) - 2)
                max_nights = min(7, len(ordered) - checkin_pos - 1)
                checkout_pos = min(checkin_pos + random.randint(1, max(1, max_nights)), len(ordered) - 1)
                if ordered[checkout_pos][0] <= ordered[checkin_pos][0] and checkin_pos + 1 < len(ordered):
                    checkout_pos = checkin_pos + 1
                logical = ordered[checkout_pos][0] > ordered[checkin_pos][0]
                return ordered[checkin_pos][1], ordered[checkout_pos][1], logical

        # Fallback: DOM-order selection.
        checkin_idx = min(4, len(days) - 2)
        checkout_idx = min(checkin_idx + 4, len(days) - 1)
        if checkout_idx <= checkin_idx and len(days) >= 2:
            checkout_idx = min(checkin_idx + 1, len(days) - 1)
        return days[checkin_idx], days[checkout_idx], checkout_idx > checkin_idx

    def _click_day_candidate(self, candidate: dict) -> bool:
        if not candidate:
            return False

        # Primary path: click by viewport coordinate captured at discovery time.
        # This works for both button-based and cell-based calendar UIs.
        try:
            x = float(candidate.get("x"))
            y = float(candidate.get("y"))
            self.page.mouse.click(x, y)
            return True
        except Exception:
            pass

        try:
            clicked = self.page.evaluate(
                """
                (payload) => {
                    const selectors = payload.selectors || [];
                    const cand = payload.candidate || {};
                    const seen = new Set();
                    const nodes = [];

                    const norm = (v) => (v || '').trim().toLowerCase();
                    const isVisible = (el) => {
                        if (!el) return false;
                        const r = el.getBoundingClientRect();
                        if (!r || r.width <= 0 || r.height <= 0) return false;
                        const style = window.getComputedStyle(el);
                        if (!style) return false;
                        if (style.display === 'none' || style.visibility === 'hidden') return false;
                        return true;
                    };
                    const isEnabled = (el) => {
                        if (!el) return false;
                        const checks = [
                            el,
                            el.closest('button, [role="button"], td, [role="gridcell"]'),
                            el.parentElement,
                        ].filter(Boolean);
                        for (const node of checks) {
                            if (node.hasAttribute('disabled')) return false;
                            const ariaDisabled = (node.getAttribute('aria-disabled') || '').trim().toLowerCase();
                            if (ariaDisabled === 'true') return false;
                            if ((node.getAttribute('data-is-day-blocked') || '').toLowerCase() === 'true') return false;
                            if ((node.getAttribute('data-disabled') || '').toLowerCase() === 'true') return false;
                            if ((node.getAttribute('data-unavailable') || '').toLowerCase() === 'true') return false;
                        }
                        return true;
                    };

                    for (const sel of selectors) {
                        for (const el of document.querySelectorAll(sel)) {
                            if (seen.has(el)) continue;
                            seen.add(el);
                            nodes.push(el);
                        }
                    }

                    const clickTarget = (target) => {
                        if (!target || !isVisible(target) || !isEnabled(target)) return false;
                        target.scrollIntoView({ behavior: 'auto', block: 'center', inline: 'center' });
                        try {
                            target.click();
                            return true;
                        } catch (e) {}
                        try {
                            target.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                            return true;
                        } catch (e) {}
                        return false;
                    };

                    const domIndex = Number.isInteger(cand.dom_index) ? cand.dom_index : -1;
                    if (domIndex >= 0 && domIndex < nodes.length && clickTarget(nodes[domIndex])) {
                        return true;
                    }

                    const wantedLabel = norm(cand.label);
                    const wantedText = norm(cand.text);
                    const wantedTestId = norm(cand.testid);
                    const wantedDataDate = norm(cand.data_date);
                    const wantedStateDate = norm(cand.state_date);
                    const wantedTitle = norm(cand.title);

                    const matched = nodes.find((el) => {
                        if (!isVisible(el) || !isEnabled(el)) return false;
                        const label = norm(el.getAttribute('aria-label'));
                        const text = norm((el.innerText || el.textContent || '').replace(/\\s+/g, ' '));
                        const testid = norm(el.getAttribute('data-testid'));
                        const dataDate = norm(el.getAttribute('data-date'));
                        const stateDate = norm(el.getAttribute('data-state--date-string'));
                        const title = norm(el.getAttribute('title'));
                        if (wantedLabel && label === wantedLabel) return true;
                        if (wantedTestId && testid === wantedTestId) return true;
                        if (wantedDataDate && dataDate === wantedDataDate) return true;
                        if (wantedStateDate && stateDate === wantedStateDate) return true;
                        if (wantedTitle && title === wantedTitle) return true;
                        if (wantedText && text === wantedText) return true;
                        return false;
                    });

                    return clickTarget(matched);
                }
                """,
                {"selectors": self.DAY_CELL_SELECTORS, "candidate": candidate},
            )
            return bool(clicked)
        except Exception:
            return False

    def _range_is_logical(self, checkin_value: str, checkout_value: str, month_label: str) -> bool:
        fallback_year, fallback_month = self._parse_month_year_label(month_label)
        checkin_dt = self._parse_date_text(checkin_value, fallback_year=fallback_year, fallback_month=fallback_month)
        checkout_dt = self._parse_date_text(checkout_value, fallback_year=fallback_year, fallback_month=fallback_month)
        if checkin_dt and checkout_dt:
            return checkout_dt > checkin_dt
        # If we cannot parse UI text reliably, keep the original non-empty validation behavior.
        return True

    def _get_date_field_value(self, field_selector: str) -> str:
        """Read the current value of a date input field."""
        try:
            el = self.page.query_selector(field_selector)
            if el:
                try:
                    value = (el.inner_text() or "").strip()
                except Exception:
                    value = ""
                if value:
                    return value
                try:
                    return (el.input_value() or "").strip()
                except Exception:
                    return ""
        except Exception:
            pass
        return ""

    def _read_date_fields(self) -> tuple[str, str]:
        checkin = ""
        checkout = ""
        for selector in self.CHECKIN_FIELD_SELECTORS:
            checkin = self._get_date_field_value(selector)
            if checkin:
                break
        for selector in self.CHECKOUT_FIELD_SELECTORS:
            checkout = self._get_date_field_value(selector)
            if checkout:
                break
        return checkin, checkout

    def _wait_for_date_fields(self, timeout_s: float = 4.0) -> tuple[str, str]:
        deadline = time.time() + timeout_s
        checkin = ""
        checkout = ""
        while time.time() < deadline:
            checkin, checkout = self._read_date_fields()
            if self._is_real_date_value(checkin) and self._is_real_date_value(checkout):
                return checkin, checkout
            time.sleep(0.25)
        return checkin, checkout

    def _read_selected_dates_from_calendar(self) -> tuple[str, str]:
        """
        Read selected check-in/check-out labels directly from calendar cells.
        Useful when Airbnb doesn't mirror values into split date fields immediately.
        """
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

    def _resolve_dates_after_selection(
        self,
        selected_checkin: str,
        selected_checkout: str,
        month_label: str,
    ) -> tuple[str, str, bool, str]:
        """
        Resolve final date strings after clicking day cells.
        Priority: input fields -> selected calendar labels -> clicked labels.
        """
        field_checkin, field_checkout = self._wait_for_date_fields(timeout_s=2.5)
        if (
            self._is_real_date_value(field_checkin)
            and self._is_real_date_value(field_checkout)
            and self._range_is_logical(field_checkin, field_checkout, month_label)
        ):
            return field_checkin, field_checkout, True, "fields"

        for _ in range(8):
            cal_checkin, cal_checkout = self._read_selected_dates_from_calendar()
            if (
                self._is_real_date_value(cal_checkin)
                and self._is_real_date_value(cal_checkout)
                and self._range_is_logical(cal_checkin, cal_checkout, month_label)
            ):
                return cal_checkin, cal_checkout, True, "calendar"
            time.sleep(0.2)

        fallback_checkin = (selected_checkin or field_checkin or cal_checkin or "").strip()
        fallback_checkout = (selected_checkout or field_checkout or cal_checkout or "").strip()
        fallback_ok = (
            self._is_real_date_value(fallback_checkin)
            and self._is_real_date_value(fallback_checkout)
            and self._range_is_logical(fallback_checkin, fallback_checkout, month_label)
        )
        return fallback_checkin, fallback_checkout, fallback_ok, "clicked"

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
            return self.save(
                False,
                "Destination missing before Step 03 and restore from checkpoint failed.",
            )

        max_selection_attempts = 8
        required_next_clicks = random.randint(3, 8)
        next_clicks_done = 0
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
            self._ensure_dates_tab_selected()

            if next_clicks_done < required_next_clicks:
                remaining_clicks = required_next_clicks - next_clicks_done
                for _ in range(remaining_clicks):
                    if self._click_next_month():
                        next_clicks_done += 1
                        time.sleep(0.5)
                    else:
                        # Modal can disappear after internal Airbnb refresh/state reset.
                        if not self._ensure_picker_open(attempts=2):
                            break
                        self._ensure_dates_tab_selected()
                        if not self._click_next_month():
                            break
                        next_clicks_done += 1
                        time.sleep(0.5)
                month_label = self._read_visible_month_label() or month_label
                print(
                    f"  Visible month: {month_label} "
                    f"(next-month moved total {next_clicks_done}/{required_next_clicks})"
                )
                if next_clicks_done < required_next_clicks:
                    print("  Could not complete required 3-8 month navigation yet, retrying...")
                    continue
            else:
                month_label = self._read_visible_month_label() or month_label
                print(f"  Visible month: {month_label} (next-month moved total {next_clicks_done}/{required_next_clicks})")

            self._ensure_dates_tab_selected()
            days = self._get_day_buttons()
            print(f"  Available day buttons: {len(days)}")
            if len(days) < 2:
                print("  Day parser returned <2 candidates; trying brute-force day click strategy...")
                bf_checkin, bf_checkout, bf_ok = self._select_dates_with_bruteforce_click()
                if not bf_ok:
                    continue
                checkin_date = bf_checkin
                checkout_date = bf_checkout
                print(f"  Brute-force check-in selected: {checkin_date}")
                print(f"  Brute-force check-out selected: {checkout_date}")

                checkin_field_val, checkout_field_val, resolved_ok, resolved_from = self._resolve_dates_after_selection(
                    checkin_date,
                    checkout_date,
                    month_label,
                )
                print(f"  Resolved check-in ({resolved_from}): '{checkin_field_val}'")
                print(f"  Resolved check-out ({resolved_from}): '{checkout_field_val}'")

                chosen_range_logical = self._range_is_logical(checkin_date, checkout_date, month_label)
                if not chosen_range_logical:
                    print("  Brute-force selected range not logical (checkout <= checkin).")

                dates_ok = (
                    resolved_ok
                    and chosen_range_logical
                    and 3 <= next_clicks_done <= 8
                )
                if dates_ok:
                    checkin_date = checkin_field_val
                    checkout_date = checkout_field_val
                    self.shared_state["selected_location"] = (
                        self.shared_state.get("chosen_suggestion")
                        or self.shared_state.get("selected_country")
                        or ""
                    )
                    self.shared_state["selected_month"] = month_label
                    self.shared_state["checkin_date"] = checkin_date
                    self.shared_state["checkout_date"] = checkout_date
                    self.checkpoint("step03_dates_selected")
                    break
                continue

            checkin_choice, checkout_choice, chosen_range_logical = self._choose_day_pair(days, month_label)
            if not checkin_choice or not checkout_choice:
                continue

            try:
                checkin_date = checkin_choice.get("label") or checkin_choice.get("text", "").strip()
                if not self._click_day_candidate(checkin_choice):
                    raise RuntimeError("Could not click selected check-in day candidate.")
                time.sleep(0.9)
                print(f"  Check-in selected: {checkin_date}")
            except Exception as exc:
                print(f"  Check-in click failed: {exc}")
                continue

            if not self._ensure_picker_open(attempts=2):
                self._open_date_picker()
                time.sleep(0.6)
            self._ensure_dates_tab_selected()

            try:
                checkout_date = checkout_choice.get("label") or checkout_choice.get("text", "").strip()
                if not self._click_day_candidate(checkout_choice):
                    # Re-evaluate candidates after check-in in case DOM changed.
                    refreshed_days = self._get_day_buttons()
                    refreshed_pair = self._choose_day_pair(refreshed_days, month_label)
                    checkout_choice = refreshed_pair[1]
                    if not checkout_choice or not self._click_day_candidate(checkout_choice):
                        raise RuntimeError("Could not click selected check-out day candidate.")
                    checkout_date = checkout_choice.get("label") or checkout_choice.get("text", "").strip()
                time.sleep(1.0)
                print(f"  Check-out selected: {checkout_date}")
            except Exception as exc:
                print(f"  Check-out click failed: {exc}")
                continue

            checkin_field_val, checkout_field_val, resolved_ok, resolved_from = self._resolve_dates_after_selection(
                checkin_date,
                checkout_date,
                month_label,
            )
            print(f"  Resolved check-in ({resolved_from}): '{checkin_field_val}'")
            print(f"  Resolved check-out ({resolved_from}): '{checkout_field_val}'")

            dates_ok = (
                resolved_ok
                and chosen_range_logical
                and 3 <= next_clicks_done <= 8
            )
            if dates_ok:
                # Store the field values for later restore/matching because those
                # are what Airbnb actually applies to the current search context.
                checkin_date = checkin_field_val
                checkout_date = checkout_field_val
                self.shared_state["selected_location"] = (
                    self.shared_state.get("chosen_suggestion")
                    or self.shared_state.get("selected_country")
                    or ""
                )
                self.shared_state["selected_month"] = month_label
                self.shared_state["checkin_date"] = checkin_date
                self.shared_state["checkout_date"] = checkout_date
                self.checkpoint("step03_dates_selected")
                break

            print("  Date values were not valid after a single selection attempt, retrying...")

        if not picker_visible:
            return self.save(
                False,
                "Date picker modal could not be found after repeated retries.",
            )

        self.shared_state["selected_month"] = month_label
        self.shared_state["checkin_date"] = checkin_date
        self.shared_state["checkout_date"] = checkout_date
        self.shared_state["selected_location"] = (
            self.shared_state.get("chosen_suggestion")
            or self.shared_state.get("selected_country")
            or ""
        )
        if dates_ok:
            self.checkpoint("step03_dates_selected")

        comment = (
            f"Date picker recovered with retries. Visible month: {month_label}. "
            f"Next-month clicks: {next_clicks_done}/{required_next_clicks}. "
            f"Check-in: {checkin_date}, Check-out: {checkout_date}. "
            f"Resolved values — checkin: '{checkin_field_val}', checkout: '{checkout_field_val}'."
        )
        selected_location = (
            self.shared_state.get("chosen_suggestion")
            or self.shared_state.get("selected_country")
            or ""
        )
        return self.save(
            dates_ok,
            comment,
            selected_location=selected_location,
            selected_month=month_label,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
        )
