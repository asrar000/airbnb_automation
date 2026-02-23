from django.contrib import admin
from django.utils.html import format_html
from .models import ResultModel, AutoSuggestionItem, ListingItem, ListingDetail, NetworkLog, ConsoleLog


class AutoSuggestionInline(admin.TabularInline):
    model = AutoSuggestionItem
    extra = 0
    readonly_fields = ("index", "text", "created_at")


class ListingItemInline(admin.TabularInline):
    model = ListingItem
    extra = 0
    readonly_fields = ("title", "price", "image_url", "created_at")


class ListingDetailInline(admin.TabularInline):
    model = ListingDetail
    extra = 0
    readonly_fields = ("title", "subtitle", "image_urls", "created_at")


class NetworkLogInline(admin.TabularInline):
    model = NetworkLog
    extra = 0
    readonly_fields = ("method", "url", "status", "resource_type", "created_at")


class ConsoleLogInline(admin.TabularInline):
    model = ConsoleLog
    extra = 0
    readonly_fields = ("log_type", "message", "created_at")


@admin.register(ResultModel)
class ResultModelAdmin(admin.ModelAdmin):
    list_display = ("id", "test_case", "url_link", "passed_icon", "comment_short", "created_at")
    list_filter = ("passed", "test_case")
    search_fields = ("test_case", "url", "comment")
    readonly_fields = ("created_at", "screenshot_preview")
    inlines = [
        AutoSuggestionInline,
        ListingItemInline,
        ListingDetailInline,
        NetworkLogInline,
        ConsoleLogInline,
    ]

    def url_link(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:40])
        return "-"
    url_link.short_description = "URL"

    def passed_icon(self, obj):
        if obj.passed:
            return format_html('<img src="/static/admin/img/icon-yes.svg" alt="Yes">')
        return format_html('<img src="/static/admin/img/icon-no.svg" alt="No">')
    passed_icon.short_description = "Passed"

    def comment_short(self, obj):
        return obj.comment[:80] + "..." if len(obj.comment) > 80 else obj.comment
    comment_short.short_description = "Comment"

    def screenshot_preview(self, obj):
        if obj.screenshot_path:
            return format_html(
                '<a href="{}" target="_blank">{}</a>', obj.screenshot_path, obj.screenshot_path
            )
        return "No screenshot"
    screenshot_preview.short_description = "Screenshot"


@admin.register(NetworkLog)
class NetworkLogAdmin(admin.ModelAdmin):
    list_display = ("method", "status", "resource_type", "url", "created_at")
    list_filter = ("method", "status", "resource_type")


@admin.register(ConsoleLog)
class ConsoleLogAdmin(admin.ModelAdmin):
    list_display = ("log_type", "message", "created_at")
    list_filter = ("log_type",)
