from reservation.models import GuestHouse

class GuestHouseService:
    """Service for guest house operations."""

    def __init__(self, db_service):
        """
        Initialize the GuestHouse service.

        Args:
            db_service (DatabaseService): Database service
        """
        self.db_service = db_service

    def create(self, name):
        """
        Create a new guest house.

        Args:
            name (str): Name of the guest house

        Returns:
            str: ID of the created guest house
        """
        session = self.db_service.get_session()
        try:
            guesthouse = GuestHouse(name=name)
            session.add(guesthouse)
            session.commit()
            return guesthouse.id
        except Exception as e:
            session.rollback()
            raise e

    def get(self, guesthouse_id):
        """
        Get a guest house by ID.

        Args:
            guesthouse_id (str): ID of the guest house

        Returns:
            GuestHouse: Guest house entity
        """
        session = self.db_service.get_session()
        try:
            guesthouse = session.query(GuestHouse).filter(GuestHouse.id == guesthouse_id).first()
            return guesthouse
        except Exception as e:
            session.rollback()
            raise e

    def get_all(self):
        """
        Get all guest houses.

        Returns:
            list: List of guest houses
        """
        session = self.db_service.get_session()
        try:
            guesthouses = session.query(GuestHouse).all()
            return guesthouses
        except Exception as e:
            session.rollback()
            raise e

    def delete(self, guesthouse_id):
        """
        Delete a guest house.

        Args:
            guesthouse_id (str): ID of the guest house to delete

        Returns:
            bool: True if deleted, False if not found
        """
        session = self.db_service.get_session()
        try:
            guesthouse = session.query(GuestHouse).filter(GuestHouse.id == guesthouse_id).first()
            if not guesthouse:
                return False

            session.delete(guesthouse)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()