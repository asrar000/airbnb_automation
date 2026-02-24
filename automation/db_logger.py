"""
Database logging helpers.
Each test step calls save_result() to persist outcomes.

All DB calls are wrapped in run_in_thread() because Django's ORM
cannot be called from within Playwright's internal event loop context.
"""
import threading
from automation.models import (
    ResultModel,
    AutoSuggestionItem,
    ListingItem,
    ListingDetail,
    NetworkLog,
    ConsoleLog,
)


def run_in_thread(fn, *args, **kwargs):
    """
    Run a callable in a plain OS thread and block until done.
    Fixes: 'You cannot call this from an async context'
    """
    result_holder = [None]
    error_holder = [None]

    def target():
        try:
            result_holder[0] = fn(*args, **kwargs)
        except Exception as exc:
            error_holder[0] = exc

    t = threading.Thread(target=target)
    t.start()
    t.join()

    if error_holder[0]:
        raise error_holder[0]
    return result_holder[0]


def save_result(
    test_case: str,
    url: str,
    passed: bool,
    comment: str,
    screenshot_path: str = "",
    selected_location: str = "",
    selected_month: str = "",
    checkin_date: str = "",
    checkout_date: str = "",
) -> ResultModel:
    """Persist a single test-step result and return the saved object."""
    def _save():
        payload = dict(
            test_case=test_case,
            url=url,
            passed=passed,
            comment=comment,
            screenshot_path=screenshot_path,
            selected_location=selected_location or "",
            selected_month=selected_month or "",
            checkin_date=checkin_date or "",
            checkout_date=checkout_date or "",
        )
        try:
            return ResultModel.objects.create(**payload)
        except Exception as exc:
            # Backward-compatible path when DB schema has not been migrated yet.
            message = str(exc).lower()
            missing_new_cols = (
                "no column named selected_location" in message
                or "no column named selected_month" in message
                or "no column named checkin_date" in message
                or "no column named checkout_date" in message
                or "unknown column" in message
            )
            if not missing_new_cols:
                raise
            payload.pop("selected_location", None)
            payload.pop("selected_month", None)
            payload.pop("checkin_date", None)
            payload.pop("checkout_date", None)
            return ResultModel.objects.create(**payload)

    result = run_in_thread(_save)
    status = "PASSED ✅" if passed else "FAILED ❌"
    print(f"  [{status}] {test_case}")
    if comment:
        print(f"           {comment[:120]}")
    return result


def save_suggestions(result: ResultModel, suggestions: list) -> None:
    """Persist auto-suggestion items linked to a result."""
    def _save():
        for idx, text in enumerate(suggestions, start=1):
            AutoSuggestionItem.objects.create(result=result, index=idx, text=text)
    run_in_thread(_save)


def save_listings(result: ResultModel, listings: list) -> None:
    """Persist scraped listing cards linked to a result."""
    def _save():
        for item in listings:
            ListingItem.objects.create(
                result=result,
                title=item.get("title", ""),
                price=item.get("price", ""),
                image_url=item.get("image_url", ""),
            )
    run_in_thread(_save)


def save_listing_detail(
    result: ResultModel,
    title: str,
    subtitle: str,
    image_urls: list,
) -> None:
    """Persist listing detail page data."""
    def _save():
        ListingDetail.objects.create(
            result=result,
            title=title,
            subtitle=subtitle,
            image_urls="\n".join(image_urls),
        )
    run_in_thread(_save)


def save_network_logs(result: ResultModel, network_requests: list) -> None:
    """Persist captured network requests (first 50 only)."""
    def _save():
        for entry in network_requests[:50]:
            NetworkLog.objects.create(
                result=result,
                method=entry.get("method", ""),
                url=entry.get("url", "")[:2000],
                status=entry.get("status"),
                resource_type=entry.get("resource_type", ""),
            )
    run_in_thread(_save)


def save_console_logs(result: ResultModel, console_messages: list) -> None:
    """Persist captured browser console messages."""
    def _save():
        for msg in console_messages:
            ConsoleLog.objects.create(
                result=result,
                log_type=msg.get("type", "log")[:10],
                message=msg.get("text", "")[:2000],
            )
    run_in_thread(_save)
