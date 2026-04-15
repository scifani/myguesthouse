import csv
import os
import logging
from typing import Optional

try:
    import pycountry
    _PYCOUNTRY_AVAILABLE = True
except ImportError:
    _PYCOUNTRY_AVAILABLE = False
    logging.warning("pycountry not available; ICAO country code resolution will be limited")

# Countries where the Italian name in Luoghi.csv differs from pycountry's English name.
# Maps Italian name (uppercase) → ISO alpha-2 code.
_ITALIAN_TO_ALPHA2 = {
    "STATI UNITI D'AMERICA": "US",
    "GRAN BRETAGNA E IRLANDA DEL NORD": "GB",
    "GRAN BRETAGNA": "GB",
    "RUSSIA": "RU",
    "COREA DEL SUD": "KR",
    "COREA DEL NORD": "KP",
    "IRAN": "IR",
    "SIRIA": "SY",
    "BIELORUSSIA": "BY",
    "MOLDAVIA": "MD",
    "MACEDONIA DEL NORD": "MK",
    "VIETNAM": "VN",
    "CINA POPOLARE": "CN",
    "CINA": "CN",
    "GIAPPONE": "JP",
    "BRASILE": "BR",
    "MESSICO": "MX",
    "EGITTO": "EG",
    "TURCHIA": "TR",
    "LIBIA": "LY",
    "GIORDANIA": "JO",
    "LIBANO": "LB",
    "ISRAELE": "IL",
    "ARABIA SAUDITA": "SA",
    "EMIRATI ARABI UNITI": "AE",
    "GERMANIA": "DE",
    "FRANCIA": "FR",
    "SPAGNA": "ES",
    "ITALIA": "IT",
    "GRECIA": "GR",
    "POLONIA": "PL",
    "UNGHERIA": "HU",
    "SVEZIA": "SE",
    "NORVEGIA": "NO",
    "DANIMARCA": "DK",
    "FINLANDIA": "FI",
    "PAESI BASSI": "NL",
    "OLANDA": "NL",
    "SVIZZERA": "CH",
    "BELGIO": "BE",
    "PORTOGALLO": "PT",
    "IRLANDA": "IE",
    "LUSSEMBURGO": "LU",
    "UCRAINA": "UA",
    "CROAZIA": "HR",
    "REPUBBLICA CECA": "CZ",
    "SLOVACCHIA": "SK",
    "AZERBAIGIAN": "AZ",
    "KAZAKISTAN": "KZ",
    "TAGIKISTAN": "TJ",
    "KIRGHIZISTAN": "KG",
    "BOSNIA ERZEGOVINA": "BA",
    "LETTONIA": "LV",
    "LITUANIA": "LT",
    "ETIOPIA": "ET",
    "KENIA": "KE",
    "CAMERUN": "CM",
    "COSTA D'AVORIO": "CI",
    "SUD AFRICA": "ZA",
    "NUOVA ZELANDA": "NZ",
    "REPUBBLICA DOMINICANA": "DO",
    "GIAMAICA": "JM",
    "FILIPPINE": "PH",
    "MALESIA": "MY",
    "CAMBOGIA": "KH",
    "BOLIVIA": "BO",
    "VENEZUELA": "VE",
    "TANZANIA": "TZ",
    "MAROCCO": "MA",
    "CILE": "CL",
    "GUINEA EQUATORIALE": "GQ",
    "COREA": "KR",
}


class TableService:
    """Loads and queries the local AlloggiatiWeb reference tables."""

    def __init__(self, tables_dir: str):
        self._municipalities: list = []  # (code, name, province)
        self._countries: list = []       # (code, name)
        self._document_types: list = []  # (code, description)
        self._icao_to_code: dict = {}    # ICAO alpha-3 → AlloggiatiWeb code

        self._load_luoghi(os.path.join(tables_dir, 'Luoghi.csv'))
        self._load_document_types(os.path.join(tables_dir, 'Tipi_Documento.csv'))
        self._build_icao_mapping()
        logging.info(
            f"TableService: {len(self._municipalities)} municipalities, "
            f"{len(self._countries)} countries, {len(self._icao_to_code)} ICAO mappings"
        )

    def _load_luoghi(self, path: str):
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                code = row['Codice'].strip()
                name = row['Descrizione'].strip()
                province = row['Provincia'].strip()
                if row.get('DataFineVal', '').strip():
                    continue  # skip expired entries
                if code.startswith('1') and province == 'ES':
                    self._countries.append((code, name))
                else:
                    self._municipalities.append((code, name, province))

    def _load_document_types(self, path: str):
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                self._document_types.append((row['Codice'].strip(), row['Descrizione'].strip()))

    def _build_icao_mapping(self):
        name_to_code = {name.upper(): code for code, name in self._countries}

        # Step 1: build alpha-2 → AlloggiatiWeb code using the Italian name overrides
        alpha2_to_code: dict = {}
        for italian_name, alpha2 in _ITALIAN_TO_ALPHA2.items():
            if italian_name in name_to_code and alpha2 not in alpha2_to_code:
                alpha2_to_code[alpha2] = name_to_code[italian_name]

        # Step 2: automatic English-name matching for any remaining countries
        if _PYCOUNTRY_AVAILABLE:
            for country in pycountry.countries:
                if country.alpha_2 not in alpha2_to_code:
                    for attr in ('name', 'common_name', 'official_name'):
                        name = getattr(country, attr, None)
                        if name and name.upper() in name_to_code:
                            alpha2_to_code[country.alpha_2] = name_to_code[name.upper()]
                            break

        # Step 3: build alpha-3 → AlloggiatiWeb code
        if _PYCOUNTRY_AVAILABLE:
            for country in pycountry.countries:
                if country.alpha_2 in alpha2_to_code:
                    self._icao_to_code[country.alpha_3] = alpha2_to_code[country.alpha_2]

    # ── search methods ────────────────────────────────────────────────────────

    def search_municipalities(self, query: str, limit: int = 15) -> list:
        """Return municipalities whose name contains *query*, prefix matches first."""
        q = query.upper()
        prefix, rest = [], []
        for c, n, p in self._municipalities:
            if q in n:
                (prefix if n.startswith(q) else rest).append((c, n, p))
        return (prefix + rest)[:limit]

    def search_countries(self, query: str, limit: int = 15) -> list:
        """Return countries whose name contains *query*, prefix matches first."""
        q = query.upper()
        prefix, rest = [], []
        for c, n in self._countries:
            if q in n:
                (prefix if n.startswith(q) else rest).append((c, n))
        return (prefix + rest)[:limit]

    def search_places(self, query: str, limit: int = 15) -> list:
        """Search both municipalities and countries (used for document issue place)."""
        q = query.upper()
        prefix, rest = [], []
        for c, n, p in self._municipalities:
            if q in n:
                entry = {'code': c, 'label': f"{n} ({p})", 'type': 'municipality'}
                (prefix if n.startswith(q) else rest).append(entry)
        for c, n in self._countries:
            if q in n:
                entry = {'code': c, 'label': n, 'type': 'country'}
                (prefix if n.startswith(q) else rest).append(entry)
        return (prefix + rest)[:limit]

    # ── lookup by code ────────────────────────────────────────────────────────

    def get_country_by_code(self, code: str) -> Optional[tuple]:
        return next(((c, n) for c, n in self._countries if c == code), None)

    def get_municipality_by_code(self, code: str) -> Optional[tuple]:
        return next(((c, n, p) for c, n, p in self._municipalities if c == code), None)

    def get_country_by_icao(self, icao3: str) -> Optional[str]:
        """Return the AlloggiatiWeb country code for an ICAO alpha-3 code, or None."""
        return self._icao_to_code.get(icao3.upper().strip('<'))

    def get_document_types(self) -> list:
        return self._document_types
