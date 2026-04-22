import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from registration.models import Base

_DATA_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(_DATA_DIR, exist_ok=True)
_DB_PATH = os.environ.get('DB_PATH', os.path.join(_DATA_DIR, 'myguesthouse.db'))

engine = create_engine(f'sqlite:///{_DB_PATH}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Schema migrations for databases created before columns were added.
with engine.connect() as _conn:
    _apt = {row[1] for row in _conn.execute(text('PRAGMA table_info(registration_apartments)'))}
    for _col, _def in [
        ('cin',          'VARCHAR(50)'),
        ('cir',          'VARCHAR(50)'),
        ('comune',       'VARCHAR(100)'),
        ('indirizzo',    'VARCHAR(200)'),
        ('ross_codice',  'VARCHAR(10)'),
        ('ross_camere',  'INTEGER'),
        ('ross_letti',   'INTEGER'),
        ('description',  'TEXT'),
        ('size',         'VARCHAR(20)'),
        ('max_guests',   'INTEGER'),
        ('features',     'TEXT'),
        ('images',       'TEXT'),
    ]:
        if _col not in _apt:
            _conn.execute(text(f'ALTER TABLE registration_apartments ADD COLUMN {_col} {_def}'))

    _rg = {row[1] for row in _conn.execute(text('PRAGMA table_info(registered_guests)'))}
    for _col, _def in [('stay_id', 'VARCHAR(36)'), ('profile_id', 'VARCHAR(36)')]:
        if _col not in _rg:
            _conn.execute(text(f'ALTER TABLE registered_guests ADD COLUMN {_col} {_def}'))

    _res = {row[1] for row in _conn.execute(text('PRAGMA table_info(reservations)'))}
    if 'status' not in _res:
        _conn.execute(text("ALTER TABLE reservations ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'"))

    _conn.commit()
