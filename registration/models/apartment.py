import json
import uuid
from sqlalchemy import Column, Integer, String, Text
from registration.models.base import Base


class Apartment(Base):
    __tablename__ = 'registration_apartments'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    aw_user = Column(String(50), nullable=False)
    aw_password = Column(String(100), nullable=False)
    aw_ws_key = Column(String(500), nullable=False)
    cin = Column(String(50), nullable=True)
    cir = Column(String(50), nullable=True)
    comune = Column(String(100), nullable=True)
    indirizzo = Column(String(200), nullable=True)
    ross_codice = Column(String(10), nullable=True)
    ross_camere = Column(Integer, nullable=True)
    ross_letti = Column(Integer, nullable=True)

    # Public website content
    description = Column(Text, nullable=True)
    size = Column(String(20), nullable=True)
    max_guests = Column(Integer, nullable=True)
    features = Column(Text, nullable=True)   # JSON array of strings
    images = Column(Text, nullable=True)     # JSON array of paths under web/static/images/

    def to_dict(self, include_credentials=False):
        d = {
            'id': self.id,
            'name': self.name,
            'aw_user': self.aw_user,
            'cin': self.cin,
            'cir': self.cir,
            'comune': self.comune,
            'indirizzo': self.indirizzo,
            'ross_codice': self.ross_codice,
            'ross_camere': self.ross_camere,
            'ross_letti': self.ross_letti,
            'description': self.description,
            'size': self.size,
            'max_guests': self.max_guests,
            'features': json.loads(self.features) if self.features else [],
            'images': json.loads(self.images) if self.images else [],
        }
        if include_credentials:
            d['aw_password'] = self.aw_password
            d['aw_ws_key'] = self.aw_ws_key
        return d
