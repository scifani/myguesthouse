import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Apartment(Base):
    """Entity class representing an apartment in the guest house."""
    __tablename__ = 'apartments'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    guesthouse_id = Column(String(36), ForeignKey('guesthouses.id'), nullable=False)

    reservations = relationship("Reservation", back_populates="apartment", cascade="all, delete-orphan")
    guesthouse = relationship("GuestHouse", back_populates="apartments")

    def __init__(self, name, id=None):
        self.id = id if id else str(uuid.uuid4())
        self.name = name

    def to_dict(self):
        """Convert apartment to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'guesthouse_id': self.guesthouse_id
        }