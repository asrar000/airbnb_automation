"""
BaseTestStep: parent class for every automation step.
All steps must implement the `run()` method.
Uses synchronous Playwright API throughout.
"""
import time
from abc import ABC, abstractmethod

from playwright.sync_api import Page

from automation.browser import take_screenshot, dismiss_popups
from automation.db_logger import save_result
from automation.models import ResultModel
from automation.runtime_state import save_checkpoint, merge_checkpoint


class BaseTestStep(ABC):
    """Abstract base class for an individual Airbnb automation step."""

    name: str = "Unnamed Step"

    def __init__(self, page: Page, url: str, shared_state: dict):
        self.page = page
        self.url = url
        self.shared_state = shared_state

    @abstractmethod
    def run(self) -> ResultModel:
        """Execute the step and return a ResultModel instance."""

    def screenshot(self, label: str) -> str:
        """Helper — take a screenshot and return its path."""
        return take_screenshot(self.page, label)

    def save(self, passed: bool, comment: str, screenshot_path: str = "") -> ResultModel:
        """Shortcut to persist a result for this step."""
        return save_result(
            test_case=self.name,
            url=self.page.url,
            passed=passed,
            comment=comment,
            screenshot_path=screenshot_path,
        )

    def wait(self, seconds: float = 1.0) -> None:
        time.sleep(seconds)

    def dismiss_popups(self) -> None:
        """
        Dismiss all visible popups on the current page.
        Expanded selector list covers the 'Got it' pricing modal
        and any other Airbnb overlay that may appear at any time.
        """
        dismiss_popups(self.page)

    def safe_dismiss_popups(self) -> None:
        """
        Silently attempt popup dismissal — never raises, safe to call anywhere.
        Use this before any important interaction to clear overlays first.
        """
        try:
            dismiss_popups(self.page)
        except Exception:
            pass

    def checkpoint(self, step_name: str) -> None:
        """Persist selected shared_state fields to runtime_state.json."""
        try:
            save_checkpoint(self.shared_state, step_name)
        except Exception:
            pass

    def restore_checkpoint(self) -> None:
        """Merge saved state into empty shared_state fields."""
        try:
            merge_checkpoint(self.shared_state)
        except Exception:
            pass
