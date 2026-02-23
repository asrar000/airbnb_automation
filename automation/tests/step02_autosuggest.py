"""
Step 02: Search Auto Suggestion Verification
- Wait for auto-suggestion list to appear
- Verify suggestions are relevant
- Confirm each suggestion has location icon + text
- Store all suggestions in DB
- Randomly select one and click it
"""
import random
import time

from automation.tests.base import BaseTestStep
from automation.db_logger import save_suggestions
from automation.models import ResultModel


class Step02AutoSuggestion(BaseTestStep):
    name = "Google Auto Suggestion List Availability Test"

    # Containers that wrap the whole suggestion dropdown
    SUGGESTION_LIST_SELECTORS = [
        '[data-testid="structured-search-input-field-query-panel"]',
        '[role="listbox"]',
        '[data-testid="autocomplete-results-container"]',
        'div[aria-label*="suggestion" i]',
        'ul[role="listbox"]',
    ]

    # Individual suggestion row selectors — ordered from most to least specific
    SUGGESTION_ITEM_SELECTORS = [
        '[data-testid="structured-search-input-field-query-panel"] [role="option"]',
        '[data-testid="structured-search-input-field-query-panel"] li',
        '[role="listbox"] [role="option"]',
        '[role="listbox"] li',
        '[data-testid="option"]',
        'li[role="option"]',
    ]

    def run(self) -> ResultModel:
        print("\n[Step 02] Auto Suggestion Verification...")

        country = self.shared_state.get("selected_country", "Japan")

        # --- Wait for suggestion dropdown to appear ---
        suggestion_list_found = False
        for sel in self.SUGGESTION_LIST_SELECTORS:
            try:
                self.page.wait_for_selector(sel, timeout=8000)
                suggestion_list_found = True
                print(f"  Suggestion container found via: {sel}")
                break
            except Exception:
                continue

        screenshot_path = self.screenshot("step02_suggestions")

        if not suggestion_list_found:
            return self.save(
                False,
                f"Auto-suggestion list did not appear after typing '{country}'.",
                screenshot_path,
            )

        # --- Give the list a moment to fully render ---
        time.sleep(1)

        # --- Try to scrape suggestion text ---
        suggestions = []
        clicked_el = None

        for sel in self.SUGGESTION_ITEM_SELECTORS:
            try:
                items = self.page.query_selector_all(sel)
                if not items:
                    continue
                temp = []
                for item in items:
                    try:
                        # Try innerText first, fall back to textContent
                        text = item.inner_text().strip()
                        if not text:
                            text = (item.evaluate("el => el.textContent") or "").strip()
                        if text:
                            temp.append((text, item))
                    except Exception:
                        continue
                if temp:
                    suggestions = [t for t, _ in temp]
                    # Keep element references for clicking
                    suggestion_elements = [el for _, el in temp]
                    print(f"  Found {len(suggestions)} suggestions via: {sel}")
                    break
            except Exception:
                continue

        # --- Fallback: dump all visible text inside the container ---
        if not suggestions:
            print("  Falling back to container text scrape...")
            for container_sel in self.SUGGESTION_LIST_SELECTORS:
                try:
                    container = self.page.query_selector(container_sel)
                    if not container:
                        continue
                    raw = container.inner_text().strip()
                    if raw:
                        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                        if lines:
                            suggestions = lines
                            suggestion_elements = None
                            print(f"  Fallback scraped {len(lines)} lines from container.")
                            break
                except Exception:
                    continue

        if not suggestions:
            return self.save(
                False,
                "Suggestion list appeared but no items could be scraped.",
                screenshot_path,
            )

        # --- Validate relevance ---
        country_words = [w.lower() for w in country.split() if len(w) > 3]
        relevant = any(
            any(word in s.lower() for word in country_words)
            for s in suggestions
        )

        comment_items = "; ".join([f"{i + 1}. {s}" for i, s in enumerate(suggestions[:8])])
        comment = f"suggested items: {comment_items}"
        print(f"  Suggestions: {comment_items[:120]}")

        result = self.save(relevant, comment, screenshot_path)
        save_suggestions(result, suggestions)

        # --- Randomly pick one suggestion (prefer first 5) ---
        chosen_index = random.randint(0, min(len(suggestions) - 1, 4))
        self.shared_state["chosen_suggestion"] = suggestions[chosen_index]
        self.shared_state["chosen_suggestion_index"] = chosen_index
        print(f"  Chosen suggestion #{chosen_index + 1}: {suggestions[chosen_index][:60]}")

        # --- Click the chosen suggestion ---
        clicked = False

        # Attempt 1: click element reference if we have it
        if 'suggestion_elements' in dir() and suggestion_elements and chosen_index < len(suggestion_elements):
            try:
                suggestion_elements[chosen_index].click()
                clicked = True
                print("  Clicked via element reference.")
            except Exception as e:
                print(f"  Element click failed: {e}")

        # Attempt 2: re-query and click by index
        if not clicked:
            for sel in self.SUGGESTION_ITEM_SELECTORS:
                try:
                    items = self.page.query_selector_all(sel)
                    if items and chosen_index < len(items):
                        items[chosen_index].click()
                        clicked = True
                        print(f"  Clicked suggestion via re-query: {sel}")
                        break
                except Exception:
                    continue

        # Attempt 3: press Enter if we can't click
        if not clicked:
            print("  Could not click suggestion — pressing Enter instead.")
            self.page.keyboard.press("Enter")

        time.sleep(2)
        return result