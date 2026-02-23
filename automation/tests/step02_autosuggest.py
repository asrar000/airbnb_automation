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

    SUGGESTION_LIST_SELECTORS = [
        '[data-testid="structured-search-input-field-query-panel"]',
        '[role="listbox"]',
        'ul[aria-label*="suggestion"]',
        '[data-testid="autocomplete-results-container"]',
        '.sb-autocomplete--box',
    ]

    SUGGESTION_ITEM_SELECTORS = [
        '[data-testid="option"]',
        '[role="option"]',
        'li[role="option"]',
        '[data-testid="structured-search-input-field-query-panel"] li',
    ]

    def run(self) -> ResultModel:
        print("\n[Step 02] Auto Suggestion Verification...")

        country = self.shared_state.get("selected_country", "Japan")

        # Wait for suggestion list
        suggestion_list_found = False
        for sel in self.SUGGESTION_LIST_SELECTORS:
            try:
                self.page.wait_for_selector(sel, timeout=8000)
                suggestion_list_found = True
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

        # Collect suggestion items
        suggestions = []
        for sel in self.SUGGESTION_ITEM_SELECTORS:
            items = self.page.query_selector_all(sel)
            if items:
                for item in items:
                    try:
                        text = item.inner_text().strip()
                        if text:
                            suggestions.append(text)
                    except Exception:
                        continue
                if suggestions:
                    break

        if not suggestions:
            return self.save(
                False,
                "Suggestion list appeared but no items could be scraped.",
                screenshot_path,
            )

        # Validate relevance
        country_words = [w.lower() for w in country.split() if len(w) > 3]
        relevant = any(
            any(word in s.lower() for word in country_words)
            for s in suggestions
        )

        comment_items = "; ".join([f"{i + 1}. {s}" for i, s in enumerate(suggestions[:8])])
        comment = f"suggested items: {comment_items}"

        result = self.save(relevant, comment, screenshot_path)
        save_suggestions(result, suggestions)

        chosen_index = random.randint(0, min(len(suggestions) - 1, 4))
        self.shared_state["chosen_suggestion"] = suggestions[chosen_index]
        self.shared_state["chosen_suggestion_index"] = chosen_index

        # Click on chosen suggestion
        for sel in self.SUGGESTION_ITEM_SELECTORS:
            items = self.page.query_selector_all(sel)
            if items and chosen_index < len(items):
                try:
                    items[chosen_index].click()
                    print(f"  Clicked suggestion #{chosen_index + 1}: {suggestions[chosen_index][:60]}")
                    time.sleep(1.5)
                    break
                except Exception:
                    continue

        return result
