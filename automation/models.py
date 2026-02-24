from django.db import models


class ResultModel(models.Model):
    """
    Stores the result of each automated test case step.
    Mirrors the Django admin dashboard shown in the assignment.
    """

    TEST_CASE_CHOICES = [
        ("landing", "Website Landing and Initial Search Setup"),
        ("autosuggest", "Google Auto Suggestion List Availability Test"),
        ("datepicker", "Date Picker Modal Open and Visibility Test"),
        ("guestpicker", "Guest Picker Interaction Test"),
        ("refinedates", "Refine Button Date Validation Test"),
        ("listinglist", "Listing Results Scrape Test"),
        ("listingdetail", "Item Details Page Verification Test"),
        ("network", "Network Monitoring Test"),
        ("console", "Console Log Monitoring Test"),
    ]

    test_case = models.CharField(max_length=255)
    url = models.URLField(max_length=500, blank=True)
    passed = models.BooleanField(default=False)
    comment = models.TextField(blank=True)
    screenshot_path = models.CharField(max_length=500, blank=True)
    selected_location = models.CharField(max_length=255, blank=True)
    selected_month = models.CharField(max_length=100, blank=True)
    checkin_date = models.CharField(max_length=100, blank=True)
    checkout_date = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Result model"
        verbose_name_plural = "Result models"
        ordering = ["-created_at"]

    def __str__(self):
        status = "✅" if self.passed else "❌"
        return f"{status} [{self.test_case}] - {self.url}"


class AutoSuggestionItem(models.Model):
    """Stores each suggestion item from the Airbnb search auto-suggest list."""

    result = models.ForeignKey(ResultModel, on_delete=models.CASCADE, related_name="suggestions")
    index = models.PositiveIntegerField()
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["index"]

    def __str__(self):
        return f"{self.index}. {self.text}"


class ListingItem(models.Model):
    """Stores scraped listing data from the search results page."""

    result = models.ForeignKey(ResultModel, on_delete=models.CASCADE, related_name="listings")
    title = models.CharField(max_length=500, blank=True)
    price = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.price}"


class ListingDetail(models.Model):
    """Stores detail page data for a single listing."""

    result = models.ForeignKey(ResultModel, on_delete=models.CASCADE, related_name="details")
    title = models.CharField(max_length=500, blank=True)
    subtitle = models.CharField(max_length=500, blank=True)
    image_urls = models.TextField(blank=True, help_text="Newline-separated image URLs")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class NetworkLog(models.Model):
    """Stores captured network requests during automation."""

    result = models.ForeignKey(ResultModel, on_delete=models.CASCADE, related_name="network_logs")
    method = models.CharField(max_length=10, blank=True)
    url = models.URLField(max_length=2000, blank=True)
    status = models.IntegerField(null=True, blank=True)
    resource_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method} {self.status} - {self.url[:80]}"


class ConsoleLog(models.Model):
    """Stores captured browser console messages during automation."""

    LOG_TYPES = [
        ("log", "Log"),
        ("warn", "Warning"),
        ("error", "Error"),
        ("info", "Info"),
    ]

    result = models.ForeignKey(ResultModel, on_delete=models.CASCADE, related_name="console_logs")
    log_type = models.CharField(max_length=10, choices=LOG_TYPES, default="log")
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.log_type.upper()}] {self.message[:100]}"
