import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from registration.models.base import Base


class RegisteredGuest(Base):
    __tablename__ = 'registered_guests'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    apartment_id = Column(String(36), nullable=False)
    apartment_name = Column(String(100))
    registered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    stay_id = Column(String(36), ForeignKey('guest_stays.id'), nullable=True)
    profile_id = Column(String(36), ForeignKey('guest_profiles.id'), nullable=True)

    stay = relationship('GuestStay', back_populates='guests')
    profile = relationship('GuestProfile')

    arrival_date = Column(String(10), nullable=False)   # YYYY-MM-DD
    num_days = Column(Integer)
    guest_type = Column(String(2))
    guest_type_label = Column(String(50))

    last_name = Column(String(50), nullable=False)
    first_name = Column(String(30), nullable=False)
    gender = Column(String(1))
    birth_date = Column(String(10))                     # dd/mm/yyyy

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

    def to_dict(self):
        return {
            'id': self.id,
            'apartment_id': self.apartment_id,
            'apartment_name': self.apartment_name,
            'registered_at': self.registered_at.strftime('%Y-%m-%dT%H:%M:%S') if self.registered_at else None,
            'arrival_date': self.arrival_date,
            'num_days': self.num_days,
            'guest_type': self.guest_type,
            'guest_type_label': self.guest_type_label,
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
