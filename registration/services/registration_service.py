import logging
import re
from registration.models.guest import Guest
from registration.services.alloggiatiweb_api import AlloggiatiWebApi

_DATE_RE = re.compile(r'^\d{2}/\d{2}/\d{4}$')

# Fixed-width field limits defined by the AlloggiatiWeb record format
_FIELD_MAX_LENGTHS = {
    'last_name': 50,
    'first_name': 30,
    'birth_city': 9,
    'birth_province': 2,
    'birth_country': 9,
    'citizenship': 9,
    'document_type': 5,
    'document_number': 20,
    'document_issue_place': 9,
}

_REQUIRED_FIELDS = [
    'last_name', 'first_name', 'gender', 'birth_date',
    'birth_country', 'citizenship',
]


class RegistrationService:
    """Validates and submits guest records to AlloggiatiWeb."""

    def __init__(self, api: AlloggiatiWebApi):
        self._api = api

    def send_guests(self, guests: list) -> AlloggiatiWebApi.Result:
        """Validate then send guest records (production submission)."""
        self._validate(guests)
        logging.info(f"Sending {len(guests)} guest(s) to AlloggiatiWeb")
        return self._api.send_schedine(guests)

    def test_guests(self, guests: list) -> AlloggiatiWebApi.Result:
        """Validate then dry-run the submission (no real police report created)."""
        self._validate(guests)
        logging.info(f"Test-sending {len(guests)} guest(s) to AlloggiatiWeb")
        return self._api.test_schedine(guests)

    def _validate(self, guests: list):
        if not guests:
            raise ValueError("Guest list is empty")

        errors = []
        for i, guest in enumerate(guests, start=1):
            label = f"Ospite {i} ({guest.last_name} {guest.first_name})"

            for field in _REQUIRED_FIELDS:
                if not getattr(guest, field, ''):
                    errors.append(f"{label}: campo obbligatorio mancante '{field}'")

            for field, max_len in _FIELD_MAX_LENGTHS.items():
                value = getattr(guest, field, '') or ''
                if len(value) > max_len:
                    errors.append(
                        f"{label}: '{field}' troppo lungo ({len(value)} > {max_len})"
                    )

            if guest.num_days < 1 or guest.num_days > 30:
                errors.append(f"{label}: num_days deve essere tra 1 e 30")

            if guest.birth_date and not _DATE_RE.match(guest.birth_date):
                errors.append(f"{label}: birth_date deve essere in formato gg/mm/aaaa")

        if errors:
            raise ValueError("Errori di validazione:\n" + "\n".join(errors))
