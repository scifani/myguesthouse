"""
Flask API tests — auth, apartments, reservations, guest history.

The web.blueprints.admin module initialises its SQLAlchemy engine at import
time from DB_PATH.  We set that env var here, at module level, BEFORE any
web import so the engine points to a temporary SQLite file for the whole run.
"""
import os
import tempfile
import unittest

# ── must happen before any web import ────────────────────────────────────────
_db_fd, _db_path = tempfile.mkstemp(suffix='.db')
os.environ.update({
    'DB_PATH':         _db_path,
    'ADMIN_USERNAME':  'admin',
    'ADMIN_PASSWORD':  'testpass',
    'SECRET_KEY':      'test-secret-key',
    'CONFIG_FILE':     os.path.join(os.path.dirname(__file__), '..', 'config.yaml'),
})

from web.app import create_app                          # noqa: E402
from web.blueprints.admin import _Session               # noqa: E402
from registration.models import (                       # noqa: E402
    Apartment, GuestProfile, GuestStay, RegisteredGuest, Reservation,
)


# ── shared app instance (engine is module-level in admin.py) ─────────────────
_app = create_app()
_app.config['TESTING'] = True


def _clean_db():
    """Remove all rows from all tables between tests."""
    with _Session() as s:
        s.query(RegisteredGuest).delete()
        s.query(GuestProfile).delete()
        s.query(GuestStay).delete()
        s.query(Reservation).delete()
        s.query(Apartment).delete()
        s.commit()


def _login(client):
    return client.post('/login', data={'username': 'admin', 'password': 'testpass'},
                       follow_redirects=False)


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

class TestAuth(unittest.TestCase):

    def setUp(self):
        self.client = _app.test_client()

    def test_public_site_accessible_without_login(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_login_page_accessible_without_login(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)

    def test_admin_requires_login_redirects(self):
        r = self.client.get('/admin')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r.headers['Location'])

    def test_api_requires_login_returns_401_json(self):
        r = self.client.get('/api/apartments')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json()['error'], 'Non autenticato')

    def test_login_wrong_password_stays_on_login(self):
        r = self.client.post('/login', data={'username': 'admin', 'password': 'wrong'})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Credenziali non valide', r.data)

    def test_login_empty_password_rejected(self):
        r = self.client.post('/login', data={'username': 'admin', 'password': ''})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Credenziali non valide', r.data)

    def test_login_success_redirects_to_admin(self):
        r = _login(self.client)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/admin', r.headers['Location'])

    def test_after_login_admin_accessible(self):
        _login(self.client)
        r = self.client.get('/admin')
        self.assertEqual(r.status_code, 200)

    def test_logout_redirects_to_public(self):
        _login(self.client)
        r = self.client.get('/logout')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers['Location'], '/')

    def test_after_logout_api_returns_401(self):
        _login(self.client)
        self.client.get('/logout')
        r = self.client.get('/api/apartments')
        self.assertEqual(r.status_code, 401)


# ─────────────────────────────────────────────────────────────────────────────
# Apartments CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestApartments(unittest.TestCase):

    def setUp(self):
        _clean_db()
        self.client = _app.test_client()
        _login(self.client)

    def _create(self, **kwargs) -> dict:
        payload = {'name': 'Apt Test', 'aw_user': 'USR', 'aw_password': 'PWD', 'aw_ws_key': 'KEY'}
        payload.update(kwargs)
        r = self.client.post('/api/apartments',
                             json=payload,
                             content_type='application/json')
        self.assertEqual(r.status_code, 201)
        return r.get_json()

    def test_list_empty(self):
        r = self.client.get('/api/apartments')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [])

    def test_create_returns_201_with_id(self):
        data = self._create()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Apt Test')

    def test_create_missing_required_field_returns_400(self):
        r = self.client.post('/api/apartments',
                             json={'name': 'X', 'aw_user': 'U'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_list_after_create(self):
        self._create(name='Apt A')
        self._create(name='Apt B')
        r = self.client.get('/api/apartments')
        names = [a['name'] for a in r.get_json()]
        self.assertIn('Apt A', names)
        self.assertIn('Apt B', names)

    def test_get_by_id(self):
        apt = self._create()
        r = self.client.get(f"/api/apartments/{apt['id']}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['name'], 'Apt Test')

    def test_get_nonexistent_returns_404(self):
        r = self.client.get('/api/apartments/nonexistent-id')
        self.assertEqual(r.status_code, 404)

    def test_update_name(self):
        apt = self._create()
        r = self.client.put(f"/api/apartments/{apt['id']}",
                            json={'name': 'Renamed'},
                            content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['name'], 'Renamed')

    def test_delete(self):
        apt = self._create()
        r = self.client.delete(f"/api/apartments/{apt['id']}")
        self.assertEqual(r.status_code, 200)
        r2 = self.client.get(f"/api/apartments/{apt['id']}")
        self.assertEqual(r2.status_code, 404)

    def test_optional_fields_stored(self):
        apt = self._create(cin='IT123', cir='MAR456', comune='Porto San Giorgio',
                           indirizzo='Via Roma 1')
        r = self.client.get(f"/api/apartments/{apt['id']}")
        data = r.get_json()
        self.assertEqual(data['cin'], 'IT123')
        self.assertEqual(data['comune'], 'Porto San Giorgio')

    def test_ross1000_fields_stored(self):
        apt = self._create(ross_codice='A00001', ross_camere=2, ross_letti=4)
        r = self.client.get(f"/api/apartments/{apt['id']}")
        data = r.get_json()
        self.assertEqual(data['ross_codice'], 'A00001')
        self.assertEqual(data['ross_camere'], 2)


# ─────────────────────────────────────────────────────────────────────────────
# Reservations CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestReservations(unittest.TestCase):

    def setUp(self):
        _clean_db()
        self.client = _app.test_client()
        _login(self.client)
        # Create one apartment to use
        r = self.client.post('/api/apartments',
                             json={'name': 'A', 'aw_user': 'U', 'aw_password': 'P', 'aw_ws_key': 'K'},
                             content_type='application/json')
        self.apt_id = r.get_json()['id']

    def _create(self, checkin='2024-07-01', checkout='2024-07-08', **kwargs) -> dict:
        payload = {'apartment_id': self.apt_id,
                   'checkin_date': checkin, 'checkout_date': checkout}
        payload.update(kwargs)
        r = self.client.post('/api/reservations', json=payload,
                             content_type='application/json')
        self.assertEqual(r.status_code, 201, r.get_json())
        return r.get_json()

    def test_list_empty(self):
        r = self.client.get('/api/reservations')
        self.assertEqual(r.get_json(), [])

    def test_create_returns_201(self):
        data = self._create()
        self.assertIn('id', data)
        self.assertEqual(data['checkin_date'], '2024-07-01')
        self.assertEqual(data['checkout_date'], '2024-07-08')

    def test_create_checkout_before_checkin_returns_400(self):
        r = self.client.post('/api/reservations',
                             json={'apartment_id': self.apt_id,
                                   'checkin_date': '2024-07-08',
                                   'checkout_date': '2024-07-01'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_create_same_day_checkin_checkout_returns_400(self):
        r = self.client.post('/api/reservations',
                             json={'apartment_id': self.apt_id,
                                   'checkin_date': '2024-07-01',
                                   'checkout_date': '2024-07-01'},
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_checkout_day_can_also_be_checkin_day(self):
        """A checkout on day X must not prevent a checkin on day X for same apt."""
        self._create(checkin='2024-07-01', checkout='2024-07-07')
        data = self._create(checkin='2024-07-07', checkout='2024-07-14')
        self.assertEqual(data['checkin_date'], '2024-07-07')

    def test_optional_fields_stored(self):
        data = self._create(guest_name='Mario Rossi', num_guests='2 adulti',
                            source='Booking', price='120€/notte', notes='Piso alto')
        self.assertEqual(data['guest_name'], 'Mario Rossi')
        self.assertEqual(data['source'], 'Booking')

    def test_filter_by_month(self):
        self._create(checkin='2024-07-01', checkout='2024-07-08')
        self._create(checkin='2024-08-01', checkout='2024-08-08')
        r = self.client.get('/api/reservations?year=2024&month=7')
        results = r.get_json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['checkin_date'], '2024-07-01')

    def test_filter_by_month_includes_overlapping(self):
        """Reservation spanning month boundary should appear in both months."""
        self._create(checkin='2024-06-28', checkout='2024-07-04')
        r = self.client.get('/api/reservations?year=2024&month=7')
        self.assertEqual(len(r.get_json()), 1)

    def test_update(self):
        res = self._create()
        r = self.client.put(f"/api/reservations/{res['id']}",
                            json={'guest_name': 'Nuova Nome'},
                            content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['guest_name'], 'Nuova Nome')

    def test_delete(self):
        res = self._create()
        r = self.client.delete(f"/api/reservations/{res['id']}")
        self.assertEqual(r.status_code, 200)
        r2 = self.client.get('/api/reservations')
        self.assertEqual(r2.get_json(), [])

    def test_delete_nonexistent_returns_404(self):
        r = self.client.delete('/api/reservations/nonexistent')
        self.assertEqual(r.status_code, 404)


# ─────────────────────────────────────────────────────────────────────────────
# Guest history
# ─────────────────────────────────────────────────────────────────────────────

class TestGuestHistory(unittest.TestCase):

    def setUp(self):
        _clean_db()
        self.client = _app.test_client()
        _login(self.client)

        # Seed a couple of registered guests directly
        from datetime import datetime
        with _Session() as s:
            for i, (last, arr) in enumerate([('ROSSI', '2024-07-01'), ('BIANCHI', '2024-08-15')]):
                s.add(RegisteredGuest(
                    id=f'test-rg-{i}',
                    apartment_id='apt-1',
                    apartment_name='Appartamento A',
                    registered_at=datetime(2024, 7, 1),
                    arrival_date=arr,
                    num_days=3,
                    guest_type='16',
                    guest_type_label='Ospite Singolo',
                    last_name=last, first_name='MARIO',
                    gender='M', birth_date='01/01/1980',
                    is_italian_born=True,
                    birth_city_code='412058091', birth_city_name='ROMA',
                    birth_province='RM',
                    birth_country_code='100000100', birth_country_name='ITALIA',
                    citizenship_code='100000100', citizenship_name='ITALIANA',
                    document_type='IDENT', document_number='CA123',
                    issue_place_code='412058091', issue_place_name='ROMA',
                ))
            s.commit()

    def test_returns_all_without_filters(self):
        r = self.client.get('/api/guests/history')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()), 2)

    def test_filter_by_name(self):
        r = self.client.get('/api/guests/history?name=ROSSI')
        data = r.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['last_name'], 'ROSSI')

    def test_filter_by_date_from(self):
        r = self.client.get('/api/guests/history?date_from=2024-08-01')
        data = r.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['last_name'], 'BIANCHI')

    def test_filter_by_date_to(self):
        r = self.client.get('/api/guests/history?date_to=2024-07-31')
        data = r.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['last_name'], 'ROSSI')

    def test_filter_name_case_insensitive(self):
        r = self.client.get('/api/guests/history?name=rossi')
        self.assertEqual(len(r.get_json()), 1)

    def test_no_match_returns_empty(self):
        r = self.client.get('/api/guests/history?name=ZZZUNKNOWN')
        self.assertEqual(r.get_json(), [])


# ─────────────────────────────────────────────────────────────────────────────
# Lookup endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestLookupEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = _app.test_client()
        _login(self.client)

    def test_guest_types_returns_list(self):
        r = self.client.get('/api/guest-types')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(len(data) > 0)
        self.assertIn('code', data[0])
        self.assertIn('label', data[0])

    def test_document_types_returns_list(self):
        r = self.client.get('/api/document-types')
        data = r.get_json()
        self.assertTrue(len(data) > 0)

    def test_municipalities_short_query_empty(self):
        r = self.client.get('/api/municipalities?q=R')
        self.assertEqual(r.get_json(), [])

    def test_municipalities_returns_results(self):
        r = self.client.get('/api/municipalities?q=Roma')
        data = r.get_json()
        self.assertTrue(len(data) > 0)
        self.assertIn('code', data[0])

    def test_countries_returns_results(self):
        r = self.client.get('/api/countries?q=Ital')
        data = r.get_json()
        self.assertTrue(len(data) > 0)

    def test_holidays_returns_dict(self):
        r = self.client.get('/api/holidays/2024')
        data = r.get_json()
        self.assertIsInstance(data, dict)
        # Christmas is always a holiday in Italy
        self.assertIn('2024-12-25', data)

    def test_places_returns_results(self):
        r = self.client.get('/api/places?q=Roma')
        data = r.get_json()
        self.assertTrue(len(data) > 0)


# ─────────────────────────────────────────────────────────────────────────────
# Public site
# ─────────────────────────────────────────────────────────────────────────────

class TestPublicSite(unittest.TestCase):

    def setUp(self):
        self.client = _app.test_client()

    def test_index_renders_property_name(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Casa degli Ulivi', r.data)

    def test_index_has_navbar(self):
        r = self.client.get('/')
        self.assertIn(b'navbar', r.data)

    def test_login_link_present(self):
        r = self.client.get('/')
        self.assertIn(b'/login', r.data)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    unittest.main()
