"""Unit tests for TableService — reads real CSV files, no network needed."""
import os
import unittest

from registration.services.table_service import TableService

_TABLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'registration', 'tables')


class TestTableService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.svc = TableService(_TABLES_DIR)

    # ── municipality search ───────────────────────────────────────────────────

    def test_search_municipalities_returns_results(self):
        results = self.svc.search_municipalities('Roma')
        self.assertTrue(len(results) > 0)
        codes, names, provinces = zip(*results)
        self.assertIn('ROMA', [n.upper() for n in names])

    def test_search_municipalities_respects_limit(self):
        # The service returns at most `limit` results (default 15)
        results = self.svc.search_municipalities('a')
        self.assertLessEqual(len(results), 15)

    def test_search_municipalities_result_has_province(self):
        results = self.svc.search_municipalities('Milano')
        self.assertTrue(any(p == 'MI' for _, _, p in results))

    # ── country search ────────────────────────────────────────────────────────

    def test_search_countries_returns_results(self):
        results = self.svc.search_countries('Francia')
        self.assertTrue(len(results) > 0)

    def test_search_countries_returns_code_and_name(self):
        results = self.svc.search_countries('Ital')
        self.assertTrue(len(results) > 0)
        code, name = results[0]
        self.assertIsInstance(code, str)
        self.assertIsInstance(name, str)

    def test_italy_code_is_known(self):
        # Italy must be findable — its code is used throughout the app
        results = self.svc.search_countries('Italia')
        codes = [c for c, _ in results]
        self.assertIn('100000100', codes)

    # ── ICAO lookup ───────────────────────────────────────────────────────────

    def test_icao_ita_resolves(self):
        code = self.svc.get_country_by_icao('ITA')
        self.assertEqual(code, '100000100')

    def test_icao_fra_resolves(self):
        code = self.svc.get_country_by_icao('FRA')
        self.assertIsNotNone(code)
        self.assertTrue(code.startswith('1'))  # foreign country codes start with 1

    def test_icao_unknown_returns_none(self):
        code = self.svc.get_country_by_icao('ZZZ')
        self.assertIsNone(code)

    # ── places (municipalities + countries combined) ──────────────────────────

    def test_search_places_returns_municipalities_and_countries(self):
        results = self.svc.search_places('Roma')
        self.assertTrue(len(results) > 0)
        self.assertTrue(any(r['code'] == '412058091' for r in results))

    # ── document types ────────────────────────────────────────────────────────

    def test_get_document_types_non_empty(self):
        types = self.svc.get_document_types()
        self.assertTrue(len(types) > 0)

    def test_get_document_types_contains_passport(self):
        types = self.svc.get_document_types()
        codes = [c for c, _ in types]
        self.assertIn('PASOR', codes)


if __name__ == '__main__':
    unittest.main()
