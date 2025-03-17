import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Reservation(Base):
    """Entity class representing a reservation for an apartment."""
    __tablename__ = 'reservations'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_in_date = Column(DateTime, nullable=False)
    check_out_date = Column(DateTime, nullable=False)
    num_guests = Column(Integer, nullable=False)
    contact_name = Column(String(100), nullable=False)
    contact_number = Column(String(20), nullable=False)
    contact_email = Column(String(100), nullable=False)
    booking_mode = Column(String(20), nullable=False)
    notes = Column(Text)
    apartment_id = Column(String(36), ForeignKey('apartments.id'), nullable=False)

    apartment = relationship("Apartment", back_populates="reservations")

    def __init__(self, check_in_date, check_out_date, num_guests, contact_name,
                 contact_number, contact_email, booking_mode, notes="", id=None):
        self.id = id if id else str(uuid.uuid4())
        self.check_in_date = check_in_date
        self.check_out_date = check_out_date
        self.num_guests = num_guests
        self.contact_name = contact_name
        self.contact_number = contact_number
        self.contact_email = contact_email
        self.booking_mode = booking_mode
        self.notes = notes

    def to_dict(self):
        """Convert reservation to dictionary."""
        return {
            'id': self.id,
            'check_in_date': self.check_in_date.isoformat(),
            'check_out_date': self.check_out_date.isoformat(),
            'num_guests': self.num_guests,
            'contact_name': self.contact_name,
            'contact_number': self.contact_number,
            'contact_email': self.contact_email,
            'booking_mode': self.booking_mode,
            'notes': self.notes,
            'apartment_id': self.apartment_id
        }