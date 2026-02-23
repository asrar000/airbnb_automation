# Airbnb End-to-End Automation

A Django + Playwright project that automates a full user journey on Airbnb,
stores every step result in a SQLite database, and presents results through
Django Admin.

---

## Project Structure

```
airbnb_automation/
├── airbnb_automation/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── automation/                 # Main Django app
│   ├── models.py               # DB models (ResultModel, NetworkLog, etc.)
│   ├── admin.py                # Django admin configuration
│   ├── browser.py              # Playwright browser manager & utilities
│   ├── db_logger.py            # Helpers to persist results to DB
│   ├── tests/                  # One file per automation step
│   │   ├── base.py             # BaseTestStep (abstract)
│   │   ├── step01_landing.py
│   │   ├── step02_autosuggest.py
│   │   ├── step03_datepicker.py
│   │   ├── step04_guestpicker.py
│   │   ├── step05_refine.py
│   │   ├── step06_listing_detail.py
│   │   └── step07_monitoring.py
│   └── management/
│       └── commands/
│           └── run_automation.py
├── screenshots/
├── .env
├── requirements.txt
└── manage.py
```

---

## Requirements

- Ubuntu (non-root user)
- Python 3.10+
- pip

---

## Setup Instructions

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright browsers

```bash
playwright install chromium
sudo playwright install-deps chromium
```

### 4. Configure environment variables

Edit the `.env` file and replace `SECRET_KEY`:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
nano .env
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create a Django superuser

```bash
python manage.py createsuperuser
```

---

## Running the Automation

```bash
# Default (headless)
python manage.py run_automation

# Show browser window
python manage.py run_automation --headless False
```

---

## Viewing Results

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/admin/automation/resultmodel/

---

## Automation Steps

| Step | Name |
|------|------|
| 01 | Website Landing and Initial Search Setup |
| 02 | Google Auto Suggestion List Availability Test |
| 03 | Date Picker Modal Open and Visibility Test |
| 04 | Guest Picker Interaction Test |
| 05 | Refine Button Date Validation Test |
| 06 | Item Details Page Verification Test |
| 07 | Network and Console Monitoring Test |
