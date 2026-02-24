"""
Django management command: run_automation

Usage:
    python manage.py run_automation
    python manage.py run_automation --headless False
    python manage.py run_automation --url https://www.airbnb.com/

Runs the full Airbnb end-to-end automation journey using sync Playwright
and stores all results in the SQLite database.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

from automation.browser import BrowserManager
from automation.tests.step01_landing import Step01LandingAndSearch
from automation.tests.step02_autosuggest import Step02AutoSuggestion
from automation.tests.step03_datepicker import Step03DatePicker
from automation.tests.step04_guestpicker import Step04GuestPicker
from automation.tests.step05_refine import Step05RefineSearch
from automation.tests.step06_listing_detail import Step06ListingDetail
from automation.tests.step07_monitoring import Step07MonitoringLogs
from automation.runtime_state import clear_checkpoint


class Command(BaseCommand):
    help = "Run the full Airbnb end-to-end automation journey"

    def add_arguments(self, parser):
        parser.add_argument(
            "--headless",
            type=str,
            default=None,
            help="Run browser in headless mode: True or False (overrides .env)",
        )
        parser.add_argument(
            "--url",
            type=str,
            default=None,
            help="Target URL (overrides .env TARGET_URL)",
        )

    def handle(self, *args, **options):
        # Ensure DB schema is current before first result insert.
        call_command("migrate", interactive=False, verbosity=0)

        # Start each run with a fresh checkpoint file.
        clear_checkpoint()

        # --- Resolve settings ---
        target_url = options.get("url") or getattr(settings, "TARGET_URL", "https://www.airbnb.com/")

        headless_arg = options.get("headless")
        if headless_arg is not None:
            headless = headless_arg.strip().lower() != "false"
        else:
            headless = getattr(settings, "HEADLESS", True)

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  Airbnb End-to-End Automation Starting"))
        self.stdout.write(self.style.SUCCESS(f"  Target: {target_url}"))
        self.stdout.write(self.style.SUCCESS(f"  Headless: {headless}"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        # Override settings for this run
        settings.HEADLESS = headless

        # Shared state dict passed between all steps
        shared_state = {
            "target_url": target_url,
            "selected_country": None,
            "chosen_suggestion": None,
            "selected_location": None,
            "selected_month": None,
            "checkin_date": None,
            "checkout_date": None,
            "guest_count": 0,
            "listings": [],
        }

        steps_passed = 0
        steps_failed = 0
        results = []

        with BrowserManager() as bm:
            # Inject live references so monitoring step can access them
            shared_state["network_requests"] = bm.network_requests
            shared_state["console_messages"] = bm.console_messages

            step_classes = [
                Step01LandingAndSearch,
                Step02AutoSuggestion,
                Step03DatePicker,
                Step04GuestPicker,
                Step05RefineSearch,
                Step06ListingDetail,
                Step07MonitoringLogs,
            ]

            for StepClass in step_classes:
                try:
                    step = StepClass(
                        page=bm.page,
                        url=bm.page.url,
                        shared_state=shared_state,
                    )
                    result = step.run()
                    results.append(result)
                    if result.passed:
                        steps_passed += 1
                    else:
                        steps_failed += 1
                except Exception as exc:
                    steps_failed += 1
                    self.stderr.write(
                        self.style.ERROR(f"\n  [ERROR] {StepClass.__name__} raised: {exc}")
                    )
                    try:
                        from automation.browser import take_screenshot
                        from automation.db_logger import save_result
                        ss = take_screenshot(bm.page, f"error_{StepClass.__name__}")
                        save_result(
                            test_case=getattr(StepClass, "name", StepClass.__name__),
                            url=bm.page.url,
                            passed=False,
                            comment=f"Exception: {str(exc)[:500]}",
                            screenshot_path=ss,
                        )
                    except Exception:
                        pass

        # --- Final Summary ---
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("  AUTOMATION COMPLETE"))
        self.stdout.write(f"  Steps Passed : {steps_passed}")
        self.stdout.write(
            (self.style.ERROR if steps_failed else self.style.SUCCESS)(
                f"  Steps Failed : {steps_failed}"
            )
        )
        self.stdout.write(f"  Total Results saved to DB: {len(results)}")
        self.stdout.write(
            f"  Screenshots saved to: {getattr(settings, 'SCREENSHOT_DIR', 'screenshots/')}"
        )
        self.stdout.write("=" * 60)
        self.stdout.write(
            "\nView results in Django Admin: http://127.0.0.1:8000/admin/automation/resultmodel/"
        )
