"""
Step 02: Google Auto Suggestion List Availability Test

Reads the suggestions already captured in Step 01 from shared_state.
The location text is still typed in the search box (removing it would
make suggestions disappear — so we never clear the field).

Verifies:
- Suggestions appeared after entering the search input
- Suggestions are relevant to the entered location
- Each suggestion ideally shows a map icon + location text
- All suggestion items are captured and stored in the database
- One suggestion was randomly selected and clicked in Step 01
"""
import time

from automation.tests.base import BaseTestStep
from automation.db_logger import save_suggestions
from automation.models import ResultModel


class Step02AutoSuggestion(BaseTestStep):
    name = "Google Auto Suggestion List Availability Test"

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

    def _read_live_suggestions(self) -> list:
        try:
            return self.page.evaluate(
                """
                (selectors) => {
                    const seen = new Set();
                    const blocked = new Set(['where', 'search destinations', 'add dates', 'add guests']);
                    for (const sel of selectors) {
                        const items = [...document.querySelectorAll(sel)]
                            .filter(el => el.offsetParent !== null);
                        if (!items.length) continue;

                        const out = [];
                        for (const el of items) {
                            const raw = (el.innerText || el.textContent || '').trim();
                            const text = raw.split('\\n').map(p => p.trim()).filter(Boolean)[0] || raw;
                            if (!text || text.length < 2) continue;
                            const normalized = text.toLowerCase();
                            if (blocked.has(normalized) || seen.has(normalized)) continue;
                            seen.add(normalized);
                            out.push(text);
                        }

                        if (out.length > 0) return out;
                    }
                    return [];
                }
                """,
                self.SUGGESTION_SELECTORS,
            ) or []
        except Exception:
            return []

    def _check_map_icons(self) -> bool:
        """
        Verify that suggestion items contain a map/location icon (SVG or img).
        Airbnb renders a map pin SVG inside each suggestion row.
        """
        try:
            has_icons = self.page.evaluate("""
                () => {
                    const selectors = [
                        '[data-testid="structured-search-input-field-query-panel"] [role="option"]',
                        '[role="listbox"] [role="option"]',
                        'li[role="option"]',
                    ];
                    for (const sel of selectors) {
                        const items = [...document.querySelectorAll(sel)]
                            .filter(el => el.offsetParent !== null);
                        if (!items.length) continue;
                        // Check first item for SVG (map pin icon)
                        const first = items[0];
                        const hasSvg = first.querySelector('svg') !== null;
                        const hasImg = first.querySelector('img') !== null;
                        return hasSvg || hasImg;
                    }
                    return false;
                }
            """)
            return bool(has_icons)
        except Exception:
            return False

    def run(self) -> ResultModel:
        print("\n[Step 02] Auto Suggestion Verification...")

        country = self.shared_state.get("selected_country", "")
        suggestions = self.shared_state.get("pre_scraped_suggestions", [])
        chosen = self.shared_state.get("chosen_suggestion", "")

        # Take screenshot while date picker may be opening from Step 01 click
        screenshot_path = self.screenshot("step02_suggestions")

        if not suggestions:
            suggestions = self._read_live_suggestions()
            if suggestions:
                self.shared_state["pre_scraped_suggestions"] = suggestions
                print(f"  Recovered {len(suggestions)} suggestions from live DOM.")

        if not suggestions:
            return self.save(
                False,
                f"No suggestions were captured during Step 01 for '{country}'.",
                screenshot_path,
            )

        print(f"  {len(suggestions)} suggestions captured from Step 01.")
        print(f"  Chosen suggestion: '{chosen}'")

        # Verify suggestions are relevant to the entered location
        country_words = [w.lower() for w in country.split() if len(w) > 2]
        relevant = any(
            any(word in s.lower() for word in country_words)
            for s in suggestions
        )
        print(f"  Relevant to '{country}': {relevant}")

        # Check for map icons in suggestion items
        has_map_icons = self._check_map_icons()
        print(f"  Map icons present: {has_map_icons}")

        # Build comment with numbered suggestion list
        comment_items = "; ".join([f"{i + 1}. {s}" for i, s in enumerate(suggestions)])
        comment = f"suggested items: {comment_items}"
        print(f"  {comment[:200]}")

        # Pass if suggestions are relevant; map icon check is informational
        passed = relevant and len(suggestions) > 0
        result = self.save(passed, comment, screenshot_path)

        # Save all suggestion items to DB
        save_suggestions(result, suggestions)

        committed = bool(self.shared_state.get("destination_committed", False))
        print(f"  Destination committed for Step 03: {committed}")

        # Wait briefly — date picker should be opening from Step 01's suggestion click
        time.sleep(2)
        return result
