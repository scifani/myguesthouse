import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String
from registration.models.base import Base


class GuestProfile(Base):
    """Reusable guest data stored with explicit GDPR consent.

    Police records (RegisteredGuest) copy all fields at registration time and
    remain intact even after a profile is anonymized. Anonymization sets
    anonymized_at and nullifies all personal-data columns.
    """
    __tablename__ = 'guest_profiles'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gdpr_consent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    anonymized_at = Column(DateTime, nullable=True)

    last_name = Column(String(50))
    first_name = Column(String(30))
    gender = Column(String(1))
    birth_date = Column(String(10))           # dd/mm/yyyy

    is_italian_born = Column(Boolean, default=False)
    birth_city_code = Column(String(9))
    birth_city_name = Column(String(100))
    birth_province = Column(String(2))
    birth_country_code = Column(String(9))
    birth_country_name = Column(String(100))

    citizenship_code = Column(String(9))
    citizenship_name = Column(String(100))

    document_type = Column(String(5))
    document_number = Column(String(20))
    issue_place_code = Column(String(9))
    issue_place_name = Column(String(100))

    @property
    def is_anonymized(self) -> bool:
        return self.anonymized_at is not None

    def anonymize(self):
        """Erase all personal data fields. The row is kept for FK integrity."""
        self.anonymized_at = datetime.utcnow()
        for col in ('last_name', 'first_name', 'gender', 'birth_date',
                    'birth_city_code', 'birth_city_name', 'birth_province',
                    'birth_country_code', 'birth_country_name',
                    'citizenship_code', 'citizenship_name',
                    'document_type', 'document_number',
                    'issue_place_code', 'issue_place_name'):
            setattr(self, col, None)
        self.is_italian_born = None

    def to_dict(self):
        if self.is_anonymized:
            return {'id': self.id, 'anonymized_at': self.anonymized_at.strftime('%Y-%m-%dT%H:%M:%S')}
        return {
            'id': self.id,
            'gdpr_consent_at': self.gdpr_consent_at.strftime('%Y-%m-%dT%H:%M:%S') if self.gdpr_consent_at else None,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'gender': self.gender,
            'birth_date': self.birth_date,
            'is_italian_born': self.is_italian_born,
            'birth_city_code': self.birth_city_code,
            'birth_city_name': self.birth_city_name,
            'birth_province': self.birth_province,
            'birth_country_code': self.birth_country_code,
            'birth_country_name': self.birth_country_name,
            'citizenship_code': self.citizenship_code,
            'citizenship_name': self.citizenship_name,
            'document_type': self.document_type,
            'document_number': self.document_number,
            'issue_place_code': self.issue_place_code,
            'issue_place_name': self.issue_place_name,
        }
