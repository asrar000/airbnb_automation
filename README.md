# Airbnb End-to-End Automation

Django + Playwright automation for a full Airbnb search journey.
Each step result is saved in SQLite and viewable in Django Admin.

## What It Does

The command `python manage.py run_automation` runs 7 sequential steps:

1. Website Landing and Initial Search Setup
2. Google Auto Suggestion List Availability Test
3. Date Picker Modal Open and Visibility Test
4. Guest Picker Interaction Test
5. Refine Button Date Validation Test
6. Item Details Page Verification Test
7. Network and Console Monitoring Test

Data captured during the run is persisted to DB tables:

- `ResultModel`
- `AutoSuggestionItem`
- `ListingItem`
- `ListingDetail`
- `NetworkLog`
- `ConsoleLog`

## Current Step Behavior

- Step 01:
  - Opens Airbnb home page
  - Chooses a random destination from a predefined city list
  - Types destination and commits one suggestion
- Step 02:
  - Validates that suggestion list exists and is relevant
  - Stores all captured suggestions
- Step 03:
  - Opens date picker
  - Moves next-month 3 to 8 times (random)
  - Selects check-in / check-out
  - Saves selected month and dates in shared state + checkpoint
- Step 04:
  - Ensures location + dates are present
  - Opens guest picker and adds 2 to 5 guest entities (random)
  - Verifies guest display
  - Clicks Search
- Step 05:
  - Verifies navigation to `/s/` results page
  - Validates selected dates + guest values from page URL query
  - Scrapes listing `title`, `price`, `image_url` (up to 20)
  - Saves listings to DB
- Step 06:
  - Clicks a random listing from results
  - Waits for detail page content readiness
  - Extracts detail `title (h1)`, `subtitle (h2)`, and first 5 hero/gallery images
  - Saves detail data to DB
- Step 07:
  - Stores captured network and console logs
  - Reports counts for requests/errors/messages

## Screenshot Policy

- No screenshots in Step 01 to Step 04.
- Step 05 takes one screenshot of results page.
- Step 06 takes one screenshot after detail fields are collected.
- Step 07 does not take screenshots.
- If a step raises an exception, the command creates an error screenshot.

Screenshots are written to `SCREENSHOT_DIR` (default: `screenshots/`).

## Project Structure

```text
airbnb_automation/
├── airbnb_automation/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── automation/
│   ├── models.py
│   ├── admin.py
│   ├── browser.py
│   ├── db_logger.py
│   ├── runtime_state.py
│   ├── tests/
│   │   ├── base.py
│   │   ├── step01_landing.py
│   │   ├── step02_autosuggest.py
│   │   ├── step03_datepicker.py
│   │   ├── step04_guestpicker.py
│   │   ├── step05_refine.py
│   │   ├── step06_listing_detail.py
│   │   └── step07_monitoring.py
│   └── management/commands/run_automation.py
├── screenshots/
├── runtime_state.json
├── db.sqlite3
├── .env
├── requirements.txt
└── manage.py
```

## Requirements

- Python 3.10+
- pip
- Linux/WSL/macOS (tested primarily on Ubuntu)

## Setup

1. Create and activate venv:

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright Chromium:

```bash
playwright install chromium
sudo playwright install-deps chromium
```

4. Configure `.env` (minimum required: `SECRET_KEY`):

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

5. Run migrations and create admin user:

```bash
python3 manage.py migrate
python3 manage.py createsuperuser
```

## Environment Variables

Configured in `airbnb_automation/settings.py`:

- `SECRET_KEY`
- `DEBUG` (default: `True`)
- `ALLOWED_HOSTS` (default: `localhost,127.0.0.1`)
- `SCREENSHOT_DIR` (default: `screenshots`)
- `RUNTIME_STATE_FILE` (default: `runtime_state.json`)
- `TARGET_URL` (default: `https://www.airbnb.com/`)
- `HEADLESS` (default: `True`)

## Running

```bash
# Use .env defaults
python3 manage.py run_automation

# Override browser mode
python3 manage.py run_automation --headless False

# Override target URL
python3 manage.py run_automation --url https://www.airbnb.com/
```

`run_automation` auto-runs migrations and clears checkpoint state at the start of each run.

## Viewing Results

```bash
python3 manage.py runserver
```

Open:

- `http://127.0.0.1:8000/admin/automation/resultmodel/`
