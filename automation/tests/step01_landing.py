"""
Step 01: Website Landing and Initial Search Setup

Anti-bot bypass:
- Moves mouse to field naturally before clicking
- Types with realistic variable delays (150-350ms per char)
- Triple-clicks to select field before typing
- Random pauses between actions
- Retries typing every 5 attempts to re-trigger suggestions
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.browser import inject_popup_observer, dismiss_popups
from automation.models import ResultModel

TOP_SEARCH_DESTINATIONS = [
    "Paris",
    "London",
    "New York",
    "Rome",
    "Barcelona",
    "Tokyo",
    "Amsterdam",
    "Lisbon",
    "San Francisco",
    "Los Angeles",
    "Miami",
    "Toronto",
    "Sydney",
    "Dubai",
    "Mexico City",
    "Bangkok",
    "Istanbul",
    "Berlin",
    "Athens",
    "Seoul",
]


class Step01LandingAndSearch(BaseTestStep):
    name = "Website Landing and Initial Search Setup"

    SEARCH_TRIGGER_SELECTORS = [
        '[data-testid="structured-search-input-field-query"]',
        'button[data-testid="structured-search-input-field-query"]',
        'div[data-testid="structured-search-input-field-query"]',
        'button[aria-label*="where" i]',
        'button:has-text("Where")',
        'button:has-text("Search destinations")',
    ]

    SEARCH_INPUT_SELECTORS = [
        'input[data-testid="structured-search-input-field-query-input"]',
        '[placeholder="Search destinations"]',
        'input[name="query"]',
        'input[aria-autocomplete="list"]',
        '[data-testid="structured-search-input-field-query-panel"] input',
    ]

    SUGGESTION_SELECTORS = [
        '[data-testid="structured-search-input-field-query-panel"] [role="option"]',
        '[data-testid="structured-search-input-field-query-panel"] li',
        '[data-testid="structured-search-input-field-query-panel"] button',
        '[id*="autocomplete"] [role="option"]',
        '[id*="autocomplete"] li',
        '[role="listbox"] [role="option"]',
        '[role="listbox"] li',
        'li[role="option"]',
    ]

    def _popup_is_visible(self) -> bool:
        try:
            return bool(self.page.evaluate("""
                () => {
                    for (const btn of document.querySelectorAll('button')) {
                        if (btn.innerText.trim() === 'Got it' && btn.offsetParent !== null)
                            return true;
                    }
                    return false;
                }
            """))
        except Exception:
            return False

    def _force_close_popup(self) -> None:
        for sel in ['button:has-text("Got it")', '[aria-label="Close"]']:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=1000):
                    loc.click()
                    print(f"  [Popup] Closed via: {sel}")
                    time.sleep(0.8)
                    return
            except Exception:
                pass
        dismiss_popups(self.page)
        time.sleep(0.5)

    def _page_fully_loaded(self) -> bool:
        try:
            return bool(self.page.evaluate("""
                () => {
                    const selectors = [
                        '[data-testid="structured-search-input-field-query"]',
                        'button[aria-label*="where" i]',
                        '[placeholder="Search destinations"]',
                        'input[name="query"]',
                    ];
                    return selectors.some((sel) => {
                        const el = document.querySelector(sel);
                        return el && el.offsetParent !== null;
                    });
                }
            """))
        except Exception:
            return False

    def _find_visible_input_selector(self) -> str:
        for sel in self.SEARCH_INPUT_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    return sel
            except Exception:
                continue
        return ""

    def _open_search_input(self) -> bool:
        """Ensure the destination input is open/visible."""
        if self._find_visible_input_selector():
            return True

        for sel in self.SEARCH_TRIGGER_SELECTORS:
            try:
                loc = self.page.locator(sel).first
                if loc.is_visible(timeout=500):
                    loc.click()
                    time.sleep(0.6)
                    if self._find_visible_input_selector():
                        print(f"  Opened search input via: {sel}")
                        return True
            except Exception:
                continue

        return bool(self._find_visible_input_selector())

    def _get_field_bbox(self):
        for sel in self.SEARCH_INPUT_SELECTORS + self.SEARCH_TRIGGER_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el:
                    box = el.bounding_box()
                    if box:
                        return box
            except Exception:
                continue
        return None

    def _human_click_field(self) -> bool:
        """Move mouse naturally to field then click — avoids robotic direct click."""
        self._open_search_input()

        bbox = self._get_field_bbox()
        if bbox:
            x = bbox["x"] + bbox["width"] * random.uniform(0.3, 0.7)
            y = bbox["y"] + bbox["height"] * random.uniform(0.2, 0.8)
            self.page.mouse.move(x / 2, y / 2)
            time.sleep(random.uniform(0.1, 0.2))
            self.page.mouse.move(x, y)
            time.sleep(random.uniform(0.05, 0.15))
            self.page.mouse.click(x, y)
            print(f"  Clicked field at ({x:.0f}, {y:.0f})")
            return True
        for sel in self.SEARCH_INPUT_SELECTORS + self.SEARCH_TRIGGER_SELECTORS:
            try:
                el = self.page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    return True
            except Exception:
                continue
        return False

    def _get_field_value(self) -> str:
        try:
            for sel in self.SEARCH_INPUT_SELECTORS:
                el = self.page.query_selector(sel)
                if el:
                    val = el.input_value()
                    return val or ""
        except Exception:
            pass
        return ""

    def _set_query_via_js(self, query: str) -> bool:
        try:
            return bool(self.page.evaluate(
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
                {"value": query, "selectors": self.SEARCH_INPUT_SELECTORS},
            ))
        except Exception:
            return False

    def _clear_and_type(self, query: str) -> bool:
        """Type query and verify that the destination input actually has text."""
        self._open_search_input()

        input_sel = self._find_visible_input_selector()
        if input_sel:
            try:
                loc = self.page.locator(input_sel).first
                loc.click()
                self.page.keyboard.press("Control+a")
                self.page.keyboard.press("Backspace")
                time.sleep(random.uniform(0.2, 0.4))

                for i, char in enumerate(query):
                    self.page.keyboard.type(char)
                    if i > 0 and random.random() < 0.1:
                        time.sleep(random.uniform(0.3, 0.6))
                    else:
                        time.sleep(random.uniform(0.15, 0.35))
            except Exception:
                pass

        typed_value = self._get_field_value()
        if typed_value.strip():
            return True

        if self._set_query_via_js(query):
            time.sleep(0.4)
            return bool(self._get_field_value().strip())

        return False

    def _get_suggestion_texts(self) -> list:
        try:
            return self.page.evaluate("""
                () => {
                    const selectors = [
                        '[data-testid="structured-search-input-field-query-panel"] [role="option"]',
                        '[data-testid="structured-search-input-field-query-panel"] li',
                        '[data-testid="structured-search-input-field-query-panel"] button',
                        '[id*="autocomplete"] [role="option"]',
                        '[id*="autocomplete"] li',
                        '[role="listbox"] [role="option"]',
                        '[role="listbox"] li',
                        'li[role="option"]',
                    ];
                    const seen = new Set();
                    const blocked = new Set([
                        'where',
                        'search destinations',
                        'add dates',
                        'add guests',
                    ]);

                    for (const sel of selectors) {
                        const items = [...document.querySelectorAll(sel)]
                            .filter(el => el.offsetParent !== null);
                        if (!items.length) continue;

                        const texts = items.map(el => {
                            const raw = (el.innerText || el.textContent || '').trim();
                            return raw.split('\\n').map(l => l.trim()).filter(l => l)[0] || raw;
                        }).filter(t => t.length > 1);

                        const deduped = [];
                        for (const text of texts) {
                            const normalized = text.toLowerCase();
                            if (blocked.has(normalized) || seen.has(normalized)) continue;
                            seen.add(normalized);
                            deduped.push(text);
                        }

                        if (deduped.length > 0) return deduped;
                    }
                    return [];
                }
            """) or []
        except Exception:
            return []

    def _click_suggestion_at(self, index: int) -> bool:
        for sel in self.SUGGESTION_SELECTORS:
            try:
                loc = self.page.locator(sel)
                if loc.count() > index:
                    loc.nth(index).click(timeout=3000)
                    print(f"  Clicked suggestion via locator.nth({index})")
                    return True
            except Exception:
                continue
        for sel in self.SUGGESTION_SELECTORS:
            try:
                items = self.page.query_selector_all(sel)
                if items and index < len(items):
                    items[index].click()
                    return True
            except Exception:
                continue

        try:
            return bool(self.page.evaluate(
                """
                (payload) => {
                    const { index, selectors } = payload;
                    for (const sel of selectors) {
                        const items = [...document.querySelectorAll(sel)]
                            .filter(el => el.offsetParent !== null);
                        if (!items.length || index >= items.length) continue;
                        items[index].click();
                        return true;
                    }
                    return false;
                }
                """,
                {"index": index, "selectors": self.SUGGESTION_SELECTORS},
            ))
        except Exception:
            return False

        return False

    def _click_suggestion_by_text(self, text: str) -> bool:
        if not text:
            return False
        try:
            return bool(self.page.evaluate(
                """
                (payload) => {
                    const { wanted, selectors } = payload;
                    const norm = (v) => (v || '').trim().toLowerCase();
                    const wantedNorm = norm(wanted);

                    for (const sel of selectors) {
                        const items = [...document.querySelectorAll(sel)]
                            .filter(el => el.offsetParent !== null);
                        if (!items.length) continue;

                        // Exact match first, then partial.
                        let target = items.find((el) => {
                            const raw = (el.innerText || el.textContent || '').trim();
                            const first = raw.split('\\n').map(s => s.trim()).filter(Boolean)[0] || raw;
                            return norm(first) === wantedNorm;
                        });
                        if (!target) {
                            target = items.find((el) => {
                                const raw = (el.innerText || el.textContent || '').trim();
                                const first = raw.split('\\n').map(s => s.trim()).filter(Boolean)[0] || raw;
                                return norm(first).includes(wantedNorm);
                            });
                        }
                        if (target) {
                            target.click();
                            return true;
                        }
                    }
                    return false;
                }
                """,
                {"wanted": text, "selectors": self.SUGGESTION_SELECTORS},
            ))
        except Exception:
            return False

    def _dates_stage_visible(self) -> bool:
        try:
            return bool(self.page.evaluate("""
                () => {
                    const selectors = [
                        '[data-testid="structured-search-input-field-split-dates-0"]',
                        '[placeholder="Add dates"]',
                        'button:has-text("Add dates")',
                        '[data-testid="datepicker-portal"]',
                        'div[role="dialog"]',
                    ];
                    return selectors.some((sel) => {
                        const el = document.querySelector(sel);
                        return el && el.offsetParent !== null;
                    });
                }
            """))
        except Exception:
            return False

    def _commit_destination_with_enter(self, down_presses: int = 1) -> bool:
        self._open_search_input()
        self._human_click_field()
        time.sleep(0.4)

        presses = max(1, int(down_presses))
        for _ in range(presses):
            try:
                self.page.keyboard.press("ArrowDown")
                time.sleep(0.15)
            except Exception:
                pass

        try:
            self.page.keyboard.press("Enter")
            time.sleep(1.2)
        except Exception:
            return False

        return self._dates_stage_visible() or bool(self._get_field_value().strip())

    def run(self) -> ResultModel:
        print("\n[Step 01] Landing and Initial Search Setup...")

        self.page.context.clear_cookies()

        self.page.goto(
            self.shared_state.get("target_url", "https://www.airbnb.com/"),
            wait_until="domcontentloaded",
            timeout=60000,
        )

        inject_popup_observer(self.page)
        print("  [PopupObserver] Injected.")

        # Longer wait for React to fully render
        self.wait(5)

        try:
            self.page.evaluate(
                "() => { window.localStorage.clear(); window.sessionStorage.clear(); }"
            )
        except Exception:
            pass

        inject_popup_observer(self.page)

        # Simulate human browsing — move mouse randomly before interacting
        try:
            self.page.mouse.move(random.randint(400, 800), random.randint(200, 400))
            time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            pass

        print("  Waiting for search field...")
        for _ in range(12):
            if self._page_fully_loaded():
                print("  Search field ready.")
                break
            self.wait(1)

        if self._popup_is_visible():
            self._force_close_popup()
        self.wait(random.uniform(0.8, 1.5))

        title = self.page.title()
        homepage_ok = "airbnb" in title.lower()
        screenshot_path = self.screenshot("step01_homepage")

        if not homepage_ok:
            return self.save(False, f"Homepage did not load. Title: {title}", screenshot_path)

        destination = random.choice(TOP_SEARCH_DESTINATIONS)
        self.shared_state["selected_country"] = destination
        print(f"  Selected destination: {destination}")
        self.checkpoint("step01_destination_selected")

        if self._popup_is_visible():
            self._force_close_popup()
            self.wait(0.5)

        # Open/focus destination field
        self._open_search_input()
        self._human_click_field()
        self.wait(random.uniform(0.8, 1.2))

        if self._popup_is_visible():
            self._force_close_popup()
            self.wait(0.5)
            self._human_click_field()
            self.wait(0.8)

        # Type with realistic human speed
        print(f"  Typing '{destination}'...")
        typed_ok = self._clear_and_type(destination)
        typed_value = self._get_field_value().strip()
        print(f"  Destination input now: '{typed_value}'")

        if not typed_ok:
            print("  Input value missing after typing — retrying with direct set...")
            self._open_search_input()
            self._human_click_field()
            self.wait(0.4)
            typed_ok = self._clear_and_type(destination)
            typed_value = self._get_field_value().strip()
            print(f"  Destination input after retry: '{typed_value}'")

        # Wait after typing for Airbnb to fetch suggestions
        self.wait(random.uniform(1.5, 2.5))

        try:
            self.page.keyboard.press("ArrowDown")
            self.wait(0.4)
        except Exception:
            pass

        if self._popup_is_visible():
            self._force_close_popup()
            self.wait(0.5)
            val = self._get_field_value()
            if not val:
                print(f"  Field cleared — retyping...")
                self._open_search_input()
                self._human_click_field()
                self.wait(0.5)
                self._clear_and_type(destination)
                self.wait(1.5)

        # Wait up to 20 attempts for suggestions to appear
        print("  Waiting for suggestions...")
        suggestions = []
        for attempt in range(20):
            time.sleep(1)
            if self._popup_is_visible():
                print("  Popup appeared — closing and re-focusing...")
                self._force_close_popup()
                self.wait(0.5)
                self._open_search_input()
                self._human_click_field()
                self.wait(0.5)

            suggestions = self._get_suggestion_texts()
            if suggestions:
                print(f"  Got {len(suggestions)} suggestions on attempt {attempt + 1}.")
                break

            # Avoid disruptive retyping while suggestions are loading.
            if attempt == 4:
                try:
                    self.page.keyboard.press("ArrowDown")
                    self.wait(0.4)
                except Exception:
                    pass
            print(f"  Attempt {attempt + 1}: no suggestions yet...")

        self.shared_state["pre_scraped_suggestions"] = suggestions
        screenshot_path2 = self.screenshot("step01_typed_country")

        if not suggestions:
            return self.save(
                False,
                f"Homepage loaded, but suggestions did not appear for '{destination}'.",
                screenshot_path2,
            )

        # Click suggestion — this opens the date picker (Step 03)
        chosen_index = random.randint(0, min(len(suggestions) - 1, 4))
        chosen_text = suggestions[chosen_index]
        self.shared_state["chosen_suggestion"] = chosen_text
        self.shared_state["chosen_suggestion_index"] = chosen_index
        print(f"  Clicking suggestion #{chosen_index + 1}: '{chosen_text}'")

        selection_method = "click"
        clicked = self._click_suggestion_at(chosen_index)

        if not clicked:
            clicked = self._click_suggestion_by_text(chosen_text)
            if clicked:
                selection_method = "text_click"

        if not clicked:
            print("  Suggestion click failed — trying keyboard commit (Enter)...")
            clicked = self._commit_destination_with_enter(chosen_index + 1)
            if clicked:
                selection_method = "keyboard_enter"
                chosen_text = destination
                self.shared_state["chosen_suggestion"] = destination

        print(f"  Suggestion commit success: {clicked} (method: {selection_method})")
        self.shared_state["destination_committed"] = bool(clicked)
        self.checkpoint("step01_destination_committed")
        self.wait(2)

        if not clicked:
            return self.save(
                False,
                f"Suggestions appeared ({len(suggestions)}), but selecting "
                f"'{chosen_text}' failed (click + Enter fallback).",
                screenshot_path2,
            )

        return self.save(
            True,
            f"Homepage loaded. Title: '{title}'. Destination '{destination}' typed. "
            f"Suggestions: {len(suggestions)}. Selected: '{chosen_text}' via {selection_method}.",
            screenshot_path2,
        )
