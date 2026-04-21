# MyGuestHouse

A self-hosted web application for managing a guesthouse: calendar reservations, guest
check-in, and automatic submission of guest registration records to the Italian police
web service **AlloggiatiWeb** (SOAP API at `alloggiatiweb.poliziadistato.it`).

[![CI](https://github.com/scifani/myguesthouse/actions/workflows/ci.yml/badge.svg)](https://github.com/scifani/myguesthouse/actions/workflows/ci.yml)

---

## Features

- **Public website** — property and apartment showcase, location, contact info; fully
  customisable via a YAML config file with no code changes required
- **Reservation calendar** — per-apartment booking grid with overlap detection
- **Guest registration** — structured check-in form; optional MRZ passport scan
  (requires Tesseract); one-click submission to AlloggiatiWeb
- **GDPR-compliant guest profiles** — reusable guest data stored with explicit consent,
  erasable on request without affecting police records

---

## Requirements

- Python 3.11+
- `tesseract-ocr` (optional — only required for passport MRZ scanning)
  ```bash
  sudo apt install tesseract-ocr   # Debian/Ubuntu
  brew install tesseract            # macOS
  ```

---

## Quick start

```bash
git clone https://github.com/scifani/myguesthouse.git
cd myguesthouse

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml   # edit with your property details
cp .env.example .env                  # edit SECRET_KEY, ADMIN_PASSWORD at minimum

python3 -m web.app
# open http://localhost:5000
```

---

## Configuration

### `config.yaml` — site content

Copy `config.example.yaml` to `config.yaml` and fill in your details. This file is
gitignored; it never gets committed.

Key sections:

| Section | Purpose |
|---|---|
| `property` | Name, tagline, description, location |
| `apartments` | List of apartments shown on the public site |
| `contact` | Phone, email, WhatsApp |
| `branding.primary_color` | Any CSS colour — applied throughout the UI |

### `.env` — runtime secrets

Copy `.env.example` to `.env`. Variables:

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | **yes** | — | Flask session signing key |
| `ADMIN_USERNAME` | no | `admin` | Login username |
| `ADMIN_PASSWORD` | **yes** | — | Login password |
| `DATA_DIR` | no | `./data/` | Directory for the SQLite database |
| `DB_PATH` | no | `$DATA_DIR/myguesthouse.db` | Override DB path directly |
| `ALLOGGIATIWEB_CREDENTIALS_FILE` | no | `registration/tests/resources/alloggiatiweb_credentials.json` | AlloggiatiWeb credentials |
| `CONFIG_FILE` | no | `./config.yaml` | Override config file path |
| `PORT` | no | `5000` | HTTP port (used by gunicorn) |

### AlloggiatiWeb credentials

Create a JSON file with your apartment credentials (see
`alloggiatiweb_credentials_example.json` for the format) and point
`ALLOGGIATIWEB_CREDENTIALS_FILE` at it.

---

## Running tests

```bash
# All tests (no external services needed)
python3 -m unittest discover -v -s tests -p "test_*.py"

# AlloggiatiWeb integration tests (requires valid credentials)
python3 -m unittest registration.tests.test_alloggiatiweb

# MRZ reader (requires tesseract-ocr installed)
python3 -m unittest registration.tests.test_mrz_reader
```

The main test suite (`tests/`) covers Flask routes, authentication, CRUD operations,
validation logic, reference-data lookups, and config loading — all without any external
services or credentials.

---

## Architecture

```
registration/
  models/
    base.py             Shared SQLAlchemy DeclarativeBase
    apartment.py        Rentable unit (AlloggiatiWeb credentials, ROSS1000 fields)
    reservation.py      Booking record (calendar entry)
    guest_stay.py       Check-in event — links Reservation → RegisteredGuest rows
    guest_profile.py    Reusable guest data (GDPR consent + erasure)
    registered_guest.py Immutable police record (one per guest per stay)
    guest.py            In-memory dataclass used for SOAP submission
  services/
    alloggiatiweb_api.py  SOAP client for the Italian police registration service
    registration_service.py  Validation + submission orchestration
    table_service.py      Reference data (municipalities, countries, document types)
    mrz_reader.py         Passport MRZ extraction via PassportEye + Tesseract
  utils/
    guest_mapper.py       MRZ → Guest dataclass conversion
  tables/               CSV reference data loaded at startup

web/
  app.py                Flask app factory (create_app)
  config_loader.py      Loads config.yaml
  blueprints/
    public.py           Public website (/)
    admin.py            Admin SPA (/admin) + all /api/* routes
  templates/            Jinja2 templates (Soft UI Design System)
  static/assets/        CSS, JS, fonts (Soft UI — not on CDN)

tests/                  Unit + integration tests (unittest)
core/                   Generic DatabaseService (currently unused by web layer)
```

### Domain model

All ORM models share a single `Base` (`registration/models/base.py`). SQLite is used by
default; the schema is created automatically on first run.

| Model | Table | Purpose |
|---|---|---|
| `Apartment` | `registration_apartments` | Rentable unit |
| `Reservation` | `reservations` | Booking |
| `GuestStay` | `guest_stays` | Check-in event |
| `RegisteredGuest` | `registered_guests` | Police record — immutable |
| `GuestProfile` | `guest_profiles` | Reusable guest data — GDPR erasable |

---

## Contributing

Contributions are welcome. Please follow the steps below.

### 1. Fork and branch

```bash
git checkout -b feature/your-feature-name   # new feature
git checkout -b fix/short-description       # bug fix
```

### 2. Make your changes

- Keep changes focused — one concern per PR.
- Do not modify `config.yaml`, `.env`, or `data/` (all gitignored).
- If you add a new model or column, ensure `Base.metadata.create_all()` and any
  necessary `ALTER TABLE` migrations in `web/blueprints/admin.py` cover it.

### 3. Add or update tests

All logic must be covered by tests in `tests/`. The test suite must stay green:

```bash
python3 -m unittest discover -v -s tests -p "test_*.py"
```

Tests use an in-memory / temp SQLite database and do not require credentials or network
access. If your change touches a Flask route, add a test to `test_web_api.py`.

### 4. Open a pull request

Push your branch and open a PR against `main`. The CI workflow runs automatically. PRs
with failing tests will not be merged.

### What we are looking for

- Bug fixes, especially around AlloggiatiWeb edge cases or date handling
- Improved test coverage
- UI/UX improvements to the admin area or public site
- Internationalisation (the app is currently Italian-only)
- Docker / deployment improvements

### What does not belong in this repo

- `config.yaml` or any property-specific data
- AlloggiatiWeb credentials or personal guest data
- Changes that hardcode property-specific logic instead of making it configurable

---

## License

MIT
