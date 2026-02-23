"""
Browser setup and utility helpers.
Provides a reusable BrowserManager context manager and helper functions.
All Playwright usage is synchronous via playwright.sync_api.
"""
import time
import random
from pathlib import Path
from datetime import datetime

from django.conf import settings
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext


class BrowserManager:
    """
    Context manager that launches a Playwright browser using sync_playwright,
    attaches console and network listeners, and ensures cleanup on exit.
    """

    def __init__(self):
        self._playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.console_messages: list[dict] = []
        self.network_requests: list[dict] = []

    def __enter__(self) -> "BrowserManager":
        self._playwright = sync_playwright().start()

        headless = getattr(settings, "HEADLESS", True)

        self.browser = self._playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()

        # --- Console listener ---
        self.page.on(
            "console",
            lambda msg: self.console_messages.append(
                {"type": msg.type, "text": msg.text}
            ),
        )

        # --- Network listener ---
        self.page.on(
            "request",
            lambda req: self.network_requests.append(
                {
                    "method": req.method,
                    "url": req.url,
                    "resource_type": req.resource_type,
                    "status": None,
                }
            ),
        )
        self.page.on(
            "response",
            lambda resp: self._update_network_status(resp.url, resp.status),
        )

        return self

    def _update_network_status(self, url: str, status: int) -> None:
        for entry in reversed(self.network_requests):
            if entry["url"] == url and entry["status"] is None:
                entry["status"] = status
                break

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()
        return False  # do not suppress exceptions


# ---------------------------------------------------------------------------
# Screenshot helper
# ---------------------------------------------------------------------------

def take_screenshot(page: Page, step_name: str) -> str:
    """
    Capture a full-page screenshot, save to SCREENSHOT_DIR, return path.
    """
    screenshot_dir: Path = getattr(settings, "SCREENSHOT_DIR", Path("screenshots"))
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{step_name}_{timestamp}.png"
    filepath = screenshot_dir / filename

    page.screenshot(path=str(filepath), full_page=True)
    return str(filepath)


# ---------------------------------------------------------------------------
# Human-like typing
# ---------------------------------------------------------------------------

def human_type(page: Page, selector: str, text: str, delay_ms: int = 80) -> None:
    """Type text character by character to simulate a real user."""
    page.click(selector)
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.05, delay_ms / 1000))


# ---------------------------------------------------------------------------
# Popup / modal dismissal
# ---------------------------------------------------------------------------

def dismiss_popups(page: Page) -> None:
    """
    Try to close common Airbnb popups (translation banners, cookie notices, etc.).
    Silently ignores any selector that is not found.
    """
    popup_selectors = [
        '[aria-label="Close"]',
        '[data-testid="modal-container"] button[aria-label="Close"]',
        'button[aria-label="Dismiss"]',
        'button:has-text("Got it")',
        'button:has-text("Accept")',
        'button:has-text("Close")',
        '[data-testid="accept-btn"]',
    ]
    for sel in popup_selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                time.sleep(0.5)
        except Exception:
            pass
