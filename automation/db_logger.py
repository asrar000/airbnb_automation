"""
Database logging helpers.
Each test step calls save_result() to persist outcomes.
"""
from automation.models import (
    ResultModel,
    AutoSuggestionItem,
    ListingItem,
    ListingDetail,
    NetworkLog,
    ConsoleLog,
)


def save_result(
    test_case: str,
    url: str,
    passed: bool,
    comment: str,
    screenshot_path: str = "",
) -> ResultModel:
    """Persist a single test-step result and return the saved object."""
    result = ResultModel.objects.create(
        test_case=test_case,
        url=url,
        passed=passed,
        comment=comment,
        screenshot_path=screenshot_path,
    )
    status = "PASSED ✅" if passed else "FAILED ❌"
    print(f"  [{status}] {test_case}")
    if comment:
        print(f"           {comment[:120]}")
    return result


def save_suggestions(result: ResultModel, suggestions: list[str]) -> None:
    """Persist auto-suggestion items linked to a result."""
    for idx, text in enumerate(suggestions, start=1):
        AutoSuggestionItem.objects.create(result=result, index=idx, text=text)


def save_listings(result: ResultModel, listings: list[dict]) -> None:
    """Persist scraped listing cards linked to a result."""
    for item in listings:
        ListingItem.objects.create(
            result=result,
            title=item.get("title", ""),
            price=item.get("price", ""),
            image_url=item.get("image_url", ""),
        )


def save_listing_detail(
    result: ResultModel,
    title: str,
    subtitle: str,
    image_urls: list[str],
) -> None:
    """Persist listing detail page data."""
    ListingDetail.objects.create(
        result=result,
        title=title,
        subtitle=subtitle,
        image_urls="\n".join(image_urls),
    )


def save_network_logs(result: ResultModel, network_requests: list[dict]) -> None:
    """Persist captured network requests (first 50 to avoid huge datasets)."""
    for entry in network_requests[:50]:
        NetworkLog.objects.create(
            result=result,
            method=entry.get("method", ""),
            url=entry.get("url", "")[:2000],
            status=entry.get("status"),
            resource_type=entry.get("resource_type", ""),
        )


def save_console_logs(result: ResultModel, console_messages: list[dict]) -> None:
    """Persist captured browser console messages."""
    for msg in console_messages:
        ConsoleLog.objects.create(
            result=result,
            log_type=msg.get("type", "log")[:10],
            message=msg.get("text", "")[:2000],
        )
