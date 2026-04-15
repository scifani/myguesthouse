# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Python application to manage a guesthouse: track reservations and submit guest registration records to the Italian police web service **AlloggiatiWeb** (SOAP API at `alloggiatiweb.poliziadistato.it`). There is also a Flask web UI for the registration workflow.

## Running the project

**Web UI (registration):**
```bash
python3 -m web.app
# open http://localhost:5000
```

**AlloggiatiWeb credentials** are read from `registration/tests/resources/alloggiatiweb_credentials.json` (same format as `alloggiatiweb_credentials_example.json`). Override the path with `ALLOGGIATIWEB_CREDENTIALS_FILE`.

## Running tests

The test suite uses `unittest` and is configured in `.vscode/settings.json`. All tests require real external services (no mocking).

```bash
# All tests
python3 -m unittest discover -v -s . -p "test_*.py"

# AlloggiatiWeb API only (no system deps needed)
python3 -m unittest registration.tests.test_alloggiatiweb

# MRZ reader (requires tesseract-ocr installed on the system)
python3 -m unittest registration.tests.test_mrz_reader
```

`test_mrz_reader` fails if `tesseract-ocr` is not installed (`apt install tesseract-ocr`).

## Architecture

```
core/           DatabaseService — SQLAlchemy engine + session factory
reservation/    Apartment/GuestHouse/Reservation ORM models + CRUD services
registration/   AlloggiatiWeb client + guest model + Flask web UI
web/            Flask app (registration UI only)
```

### `registration/` module in detail

This is the active module. The end-to-end flow:

1. **`MrzReader`** (`services/mrz_reader.py`) — calls PassportEye to extract MRZ from a passport image
2. **`GuestMapper`** (`utils/guest_mapper.py`) — maps the raw MRZ object to a `Guest` dataclass; requires a `TableService` instance for ICAO→AlloggiatiWeb country code resolution
3. **`TableService`** (`services/table_service.py`) — loads `registration/tables/*.csv` once at startup; provides municipality/country search and ICAO alpha-3 lookup
4. **`RegistrationService`** (`services/registration_service.py`) — validates field lengths against the AlloggiatiWeb fixed-width format, then calls `AlloggiatiWebApi`
5. **`AlloggiatiWebApi`** (`services/alloggiatiweb_api.py`) — SOAP client; `send_schedine` is the submission method in use (not `GestioneAppartamenti`)

The Flask app in `web/app.py` wires all of these together. Table service and guest mapper are module-level singletons; the API client is initialised lazily from the credentials file.

### AlloggiatiWeb record format

`AlloggiatiWebApi._create_record()` produces a fixed-width string. Field widths and required status are documented in the docstring of that method. Key rules:
- `birth_city`: 9-char municipality code for Italian-born guests; 9-char country code for foreign-born guests
- `birth_province`: 2-char province for Italian-born; blank for foreign-born
- All codes come from `registration/tables/Luoghi.csv`

### Luoghi.csv structure

- **Italian municipalities**: all entries where `Provincia != 'ES'`
- **Foreign countries**: `Codice` starts with `'1'` and `Provincia == 'ES'`
- Italy itself: code `100000100`
- Expired entries have a non-empty `DataFineVal` and are skipped on load

### Known architectural issue

`reservation/models/apartment.py`, `reservation/models/reservation.py`, and `reservation/models/guest_house.py` each call `declarative_base()` independently. SQLAlchemy relationships require a **shared** `Base`. This must be fixed before the reservation module can be used with a real database. The `Base` in `core/services/database_service.py` should be the single shared instance.
