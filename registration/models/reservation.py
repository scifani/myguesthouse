import uuid
from sqlalchemy import Column, String, Text
from registration.models.apartment import Base


class Reservation(Base):
    __tablename__ = 'reservations'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    apartment_id = Column(String(36), nullable=False)
    checkin_date = Column(String(10), nullable=False)   # YYYY-MM-DD
    checkout_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    guest_name = Column(String(100))
    num_guests = Column(String(50))   # free text: "2 adulti", "2+2", etc.
    source = Column(String(50))       # Booking, Airbnb, Diretto, Apulia, Altro
    notes = Column(Text)
    price = Column(String(50))        # optional total/nightly price note

    def to_dict(self):
        return {
            'id': self.id,
            'apartment_id': self.apartment_id,
            'checkin_date': self.checkin_date,
            'checkout_date': self.checkout_date,
            'guest_name': self.guest_name,
            'num_guests': self.num_guests,
            'source': self.source,
            'notes': self.notes,
            'price': self.price,
        }
