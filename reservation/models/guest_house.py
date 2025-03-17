import uuid
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class GuestHouse(Base):
    """Entity class representing the guest house with multiple apartments."""
    __tablename__ = 'guesthouses'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)

    apartments = relationship("Apartment", back_populates="guesthouse", cascade="all, delete-orphan")

    def __init__(self, name, id=None):
        self.id = id if id else str(uuid.uuid4())
        self.name = name

    def to_dict(self):
        """Convert guest house to dictionary."""
        return {
            'id': self.id,
            'name': self.name
        }