import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from registration.models.base import Base


class GuestStay(Base):
    """One check-in event: links a Reservation to its RegisteredGuest records."""
    __tablename__ = 'guest_stays'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reservation_id = Column(String(36), ForeignKey('reservations.id'), nullable=True)
    apartment_id = Column(String(36), ForeignKey('registration_apartments.id'), nullable=False)
    checked_in_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

    reservation = relationship('Reservation', back_populates='stays')
    guests = relationship('RegisteredGuest', back_populates='stay', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'apartment_id': self.apartment_id,
            'checked_in_at': self.checked_in_at.strftime('%Y-%m-%dT%H:%M:%S') if self.checked_in_at else None,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%dT%H:%M:%S') if self.submitted_at else None,
        }
