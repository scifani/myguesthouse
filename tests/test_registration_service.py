"""Unit tests for RegistrationService validation — no external services needed."""
import unittest
from datetime import datetime

from registration.models.guest import Guest, GuestGender, GuestType
from registration.services.registration_service import RegistrationService


def _guest(**kwargs) -> Guest:
    defaults = dict(
        guest_type=GuestType.SINGLE,
        arrival_date=datetime(2024, 7, 1),
        num_days=3,
        last_name='ROSSI',
        first_name='MARIO',
        gender=GuestGender.MALE,
        birth_date='01/01/1980',
        birth_city='412058091',
        birth_province='RM',
        birth_country='100000100',
        citizenship='100000100',
        document_type='IDENT',
        document_number='CA91673EW',
        document_issue_place='412058091',
    )
    defaults.update(kwargs)
    return Guest(**defaults)


class TestRegistrationServiceValidation(unittest.TestCase):

    def setUp(self):
        self.svc = RegistrationService(api=None)  # API not called during validation

    # ── empty list ────────────────────────────────────────────────────────────

    def test_empty_list_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([])
        self.assertIn('empty', str(ctx.exception).lower())

    # ── required fields ───────────────────────────────────────────────────────

    def test_missing_last_name_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(last_name='')])
        self.assertIn('last_name', str(ctx.exception))

    def test_missing_first_name_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(first_name='')])
        self.assertIn('first_name', str(ctx.exception))

    def test_missing_citizenship_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(citizenship='')])
        self.assertIn('citizenship', str(ctx.exception))

    def test_missing_birth_country_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(birth_country='')])
        self.assertIn('birth_country', str(ctx.exception))

    # ── field length limits ───────────────────────────────────────────────────

    def test_last_name_too_long_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(last_name='A' * 51)])
        self.assertIn('last_name', str(ctx.exception))

    def test_last_name_at_limit_ok(self):
        self.svc._validate([_guest(last_name='A' * 50)])  # should not raise

    def test_document_number_too_long_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(document_number='X' * 21)])
        self.assertIn('document_number', str(ctx.exception))

    def test_birth_city_too_long_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(birth_city='1234567890')])  # 10 chars > 9
        self.assertIn('birth_city', str(ctx.exception))

    # ── num_days range ────────────────────────────────────────────────────────

    def test_num_days_zero_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(num_days=0)])
        self.assertIn('num_days', str(ctx.exception))

    def test_num_days_31_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(num_days=31)])
        self.assertIn('num_days', str(ctx.exception))

    def test_num_days_boundary_ok(self):
        self.svc._validate([_guest(num_days=1)])
        self.svc._validate([_guest(num_days=30)])

    # ── birth_date format ─────────────────────────────────────────────────────

    def test_birth_date_wrong_format_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([_guest(birth_date='1980-01-01')])  # ISO not allowed
        self.assertIn('birth_date', str(ctx.exception))

    def test_birth_date_correct_format_ok(self):
        self.svc._validate([_guest(birth_date='01/01/1980')])

    # ── multiple guests — all errors collected ─────────────────────────────────

    def test_multiple_errors_collected(self):
        bad1 = _guest(last_name='')
        bad2 = _guest(num_days=0)
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate([bad1, bad2])
        msg = str(ctx.exception)
        self.assertIn('last_name', msg)
        self.assertIn('num_days', msg)

    # ── valid guest passes without exception ─────────────────────────────────

    def test_valid_guest_ok(self):
        self.svc._validate([_guest()])


if __name__ == '__main__':
    unittest.main()
