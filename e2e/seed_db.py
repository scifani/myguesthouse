"""
Seeds a fresh SQLite database for Playwright e2e runs.

Invoked by e2e/global-setup.js before the Flask dev server starts, with
DB_PATH already pointed at a throwaway file. Fixture IDs/values referenced
by the specs live in e2e/support/fixtures.js — keep the two in sync.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web.db import Session as _Session               # noqa: E402
from registration.models import Apartment, RegisteredGuest  # noqa: E402

APARTMENT_ID = 'e2e-apt-1'
APARTMENT_NAME = 'E2E Appartamento'
ROSS_CODICE = 'V00999'

with _Session() as s:
    s.add(Apartment(
        id=APARTMENT_ID,
        name=APARTMENT_NAME,
        aw_user='e2e-user',
        aw_password='e2e-password',
        aw_ws_key='e2e-ws-key',
        ross_codice=ROSS_CODICE,
        ross_camere=2,
        ross_letti=4,
    ))

    # A stay fully inside the export range (2026-05-10..2026-05-20): should
    # always appear in the exported XML.
    s.add(RegisteredGuest(
        id='e2e-guest-in-range',
        apartment_id=APARTMENT_ID,
        apartment_name=APARTMENT_NAME,
        registered_at=datetime(2026, 5, 12),
        arrival_date='2026-05-12',
        num_days=3,
        guest_type='16',
        guest_type_label='Ospite Singolo',
        last_name='INRANGE', first_name='GUEST',
        gender='M', birth_date='01/01/1980',
        is_italian_born=True,
        birth_city_code='412058091', birth_city_name='ROMA', birth_province='RM',
        citizenship_code='100000100', citizenship_name='ITALIA',
        document_type='CARTAI', document_number='AA1111111',
    ))

    # A stay that started before the export range but is still ongoing when
    # it opens (arrival 2026-05-08, 3 nights -> departs 2026-05-11, after the
    # 2026-05-10 range start). This is exactly the case the fix targets:
    # an old implementation that only matched guests already in the current
    # check-in form would miss this one entirely.
    s.add(RegisteredGuest(
        id='e2e-guest-overlap-start',
        apartment_id=APARTMENT_ID,
        apartment_name=APARTMENT_NAME,
        registered_at=datetime(2026, 5, 8),
        arrival_date='2026-05-08',
        num_days=3,
        guest_type='16',
        guest_type_label='Ospite Singolo',
        last_name='OVERLAP', first_name='GUEST',
        gender='F', birth_date='02/02/1985',
        is_italian_born=True,
        birth_city_code='412058091', birth_city_name='ROMA', birth_province='RM',
        citizenship_code='100000100', citizenship_name='ITALIA',
        document_type='CARTAI', document_number='AA2222222',
    ))

    # A stay entirely outside the export range: must NOT appear.
    s.add(RegisteredGuest(
        id='e2e-guest-out-of-range',
        apartment_id=APARTMENT_ID,
        apartment_name=APARTMENT_NAME,
        registered_at=datetime(2026, 6, 1),
        arrival_date='2026-06-01',
        num_days=2,
        guest_type='16',
        guest_type_label='Ospite Singolo',
        last_name='OUTOFRANGE', first_name='GUEST',
        gender='M', birth_date='03/03/1990',
        is_italian_born=True,
        birth_city_code='412058091', birth_city_name='ROMA', birth_province='RM',
        citizenship_code='100000100', citizenship_name='ITALIA',
        document_type='CARTAI', document_number='AA3333333',
    ))

    s.commit()

print(f'Seeded {APARTMENT_ID} ({APARTMENT_NAME}) with 3 registered guests.')
