from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DatabaseService:
    """Service for database operations."""

    def __init__(self, connection_string):
        """
        Initialize the database service.

        Args:
            connection_string (str): SQLAlchemy connection string
        """
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get a new session."""
        return self.session()