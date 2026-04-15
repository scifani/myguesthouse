import logging
from datetime import datetime

from registration.models.guest import Guest, GuestType, GuestGender
from registration.services.table_service import TableService

# Maps the first character of the MRZ type field to an AlloggiatiWeb document code.
# Users can correct the pre-filled value in the form.
_MRZ_TYPE_TO_DOC_CODE = {
    'P': 'PASOR',  # Passaporto Ordinario
    'I': 'IDELE',  # Carta d'Identità Elettronica (default for ID cards)
    'C': 'IDENT',  # Carta di Identità (older format)
    'A': 'PASOR',  # fallback
    'V': 'PASOR',  # fallback
}

_ITALY_ICAO = 'ITA'


class GuestMapper:
    """Maps a PassportEye MRZ result to a Guest dataclass."""

    def __init__(self, table_service: TableService):
        self._tables = table_service

    def from_mrz(self, mrz, guest_type: GuestType,
                 arrival_date: datetime, num_days: int) -> Guest:
        """
        Convert a PassportEye MRZ object to a Guest.

        For Italian-born guests, birth_city and birth_province are left empty
        because the MRZ does not carry that information — the user must complete
        them in the UI using the municipality search.

        For foreign-born guests, birth_city is set to the birth_country code
        (as required by AlloggiatiWeb) and birth_province is left blank.
        """
        if mrz is None:
            raise ValueError("MRZ data is None")

        d = mrz.to_dict()
        logging.debug(f"MRZ dict: {d}")

        surname = d.get('surname', '').replace('<', ' ').strip()
        names = d.get('names', '').replace('<', ' ').strip()

        sex = d.get('sex', '<')
        if sex == 'M':
            gender = GuestGender.MALE
        elif sex == 'F':
            gender = GuestGender.FEMALE
        else:
            gender = GuestGender.UNKNOWN

        birth_date = _parse_mrz_date(d.get('date_of_birth', ''))

        nationality_icao = d.get('nationality', '').strip('<').strip()
        country_icao = d.get('country', '').strip('<').strip()

        citizenship_code = self._tables.get_country_by_icao(nationality_icao) or ''
        birth_country_code = self._tables.get_country_by_icao(country_icao) or ''

        is_italian_born = (country_icao == _ITALY_ICAO)

        mrz_type = d.get('type', 'P')
        doc_type_char = mrz_type[0].upper() if mrz_type else 'P'
        doc_type_code = _MRZ_TYPE_TO_DOC_CODE.get(doc_type_char, 'PASOR')

        doc_number = d.get('number', '').strip('<').strip()

        if is_italian_born:
            birth_city = ''
            birth_province = ''
        else:
            birth_city = birth_country_code
            birth_province = ''

        return Guest(
            guest_type=guest_type,
            arrival_date=arrival_date,
            num_days=num_days,
            last_name=surname,
            first_name=names,
            gender=gender,
            birth_date=birth_date,
            birth_city=birth_city,
            birth_province=birth_province,
            birth_country=birth_country_code,
            citizenship=citizenship_code,
            document_type=doc_type_code,
            document_number=doc_number,
            document_issue_place='',  # not in MRZ — must be filled manually
        )


def _parse_mrz_date(yymmdd: str) -> str:
    """Convert a YYMMDD MRZ date string to the dd/mm/yyyy format expected by AlloggiatiWeb."""
    s = yymmdd.strip('<').strip()
    if len(s) < 6:
        return ''
    try:
        yy = int(s[0:2])
        mm = int(s[2:4])
        dd = int(s[4:6])
        year = 2000 + yy if yy <= 30 else 1900 + yy
        return f"{dd:02d}/{mm:02d}/{year}"
    except ValueError:
        return ''
