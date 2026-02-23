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


class BaseTestStep(ABC):
    """Abstract base class for an individual Airbnb automation step."""

    name: str = "Unnamed Step"

    def __init__(self, page: Page, url: str, shared_state: dict):
        """
        :param page: Active Playwright sync Page object.
        :param url: Current page URL to store with result.
        :param shared_state: Dict shared across all steps for passing data
                             (e.g. selected country, chosen dates, guest count).
        """
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
        dismiss_popups(self.page)
