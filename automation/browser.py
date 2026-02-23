"""
Browser setup and utility helpers.
"""
import time
import random
from pathlib import Path
from datetime import datetime

from django.conf import settings
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# JavaScript that injects a MutationObserver into the page.
# It watches the DOM and the moment a "Got it" button or X close button
# appears, it clicks it automatically — no polling needed.
POPUP_OBSERVER_SCRIPT = """
() => {
    if (window.__popupObserverActive) return;
    window.__popupObserverActive = true;

    const isVisible = (el) => {
        if (!el) return false;
        return el.offsetParent !== null;
    };

    const isModalControl = (el) => {
        if (!el) return false;
        return Boolean(
            el.closest('[role="dialog"], [aria-modal="true"], [data-testid*="modal"], [data-plugin-in-point-id*="MODAL"]')
        );
    };

    function dismissPopup() {
        const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));

        // Try explicit consent/dismiss action first.
        for (const btn of buttons) {
            if (!isVisible(btn)) continue;
            const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
            if (text === 'got it' || text === 'ok' || text === 'okay') {
                btn.click();
                console.log('[PopupObserver] Clicked consent button');
                return true;
            }
        }

        // Then close controls, only when inside an actual modal/dialog.
        for (const btn of buttons) {
            if (!isVisible(btn) || !isModalControl(btn)) continue;
            const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
            const aria = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
            if (text === 'close' || text === 'dismiss' || aria.includes('close') || aria.includes('dismiss')) {
                btn.click();
                console.log('[PopupObserver] Clicked modal close');
                return true;
            }
        }

        return false;
    }

    // Run once immediately in case popup already exists
    dismissPopup();

    // Watch for any future DOM changes
    const observer = new MutationObserver(() => {
        dismissPopup();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });

    window.__popupObserver = observer;
    console.log('[PopupObserver] Started.');
}
"""


def inject_popup_observer(page: Page) -> None:
    """Inject the MutationObserver into the current page."""
    try:
        page.evaluate(POPUP_OBSERVER_SCRIPT)
    except Exception:
        pass


def dismiss_popups(page: Page) -> None:
    """Manual one-shot popup dismissal — call this as a safety net."""
    try:
        page.evaluate("""
            () => {
                const isVisible = (el) => el && el.offsetParent !== null;
                const isModalControl = (el) => Boolean(
                    el.closest('[role="dialog"], [aria-modal="true"], [data-testid*="modal"], [data-plugin-in-point-id*="MODAL"]')
                );

                const buttons = Array.from(document.querySelectorAll('button, [role="button"]'));
                for (const btn of buttons) {
                    if (!isVisible(btn)) continue;
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    if (text === 'got it' || text === 'ok' || text === 'okay') {
                        btn.click(); return 'consent';
                    }
                }

                for (const btn of buttons) {
                    if (!isVisible(btn) || !isModalControl(btn)) continue;
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    const aria = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
                    if (text === 'close' || text === 'dismiss' || aria.includes('close') || aria.includes('dismiss')) {
                        btn.click(); return 'modal-close';
                    }
                }
            }
        """)
    except Exception:
        pass
    for sel in ['button:has-text("Got it")', '[aria-label="Close"]']:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=500):
                loc.click()
                time.sleep(0.5)
                break
        except Exception:
            pass


class BrowserManager:
    def __init__(self):
        self._playwright = None
        self._display = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.console_messages: list[dict] = []
        self.network_requests: list[dict] = []

    def __enter__(self) -> "BrowserManager":
        self._playwright = sync_playwright().start()

        want_headless = getattr(settings, "HEADLESS", True)
        if want_headless:
            self._display = _start_virtual_display()
            headless = False if self._display else True
        else:
            headless = False

        self.browser = self._playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1440,900",
            ],
        )

        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
                ),
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )

        # Inject popup observer on every new page/navigation automatically
        self.context.add_init_script(f"""
            Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
            Object.defineProperty(navigator, 'plugins', {{ get: () => [1, 2, 3] }});
            Object.defineProperty(navigator, 'languages', {{ get: () => ['en-US', 'en'] }});
            window.chrome = {{ runtime: {{}} }};

            // Auto-dismiss popup observer — runs on every page load
            window.addEventListener('DOMContentLoaded', {POPUP_OBSERVER_SCRIPT});
            // Also run after full load
            window.addEventListener('load', {POPUP_OBSERVER_SCRIPT});
        """)

        self.page = self.context.new_page()

        # Re-inject observer after any navigation
        self.page.on("domcontentloaded", lambda: inject_popup_observer(self.page))
        self.page.on("load", lambda: inject_popup_observer(self.page))

        self.page.on(
            "console",
            lambda msg: self.console_messages.append({"type": msg.type, "text": msg.text}),
        )
        self.page.on(
            "request",
            lambda req: self.network_requests.append({
                "method": req.method,
                "url": req.url,
                "resource_type": req.resource_type,
                "status": None,
            }),
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
        if self._display:
            try:
                self._display.stop()
            except Exception:
                pass
        return False


def _start_virtual_display():
    try:
        from pyvirtualdisplay import Display
        display = Display(visible=False, size=(1440, 900))
        display.start()
        print("  [Browser] Virtual display started (Xvfb).")
        return display
    except Exception as e:
        print(f"  [Browser] Virtual display unavailable ({e}), using headless mode.")
        return None


def take_screenshot(page: Page, step_name: str) -> str:
    screenshot_dir: Path = getattr(settings, "SCREENSHOT_DIR", Path("screenshots"))
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{step_name}_{timestamp}.png"
    filepath = screenshot_dir / filename
    page.screenshot(path=str(filepath), full_page=True)
    return str(filepath)


def human_type(page: Page, selector: str, text: str, delay_ms: int = 80) -> None:
    page.click(selector)
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.05, delay_ms / 1000))
