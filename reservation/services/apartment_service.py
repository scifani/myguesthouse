from reservation.models import Apartment, GuestHouse

class ApartmentService:
    """Service for apartment operations."""

    def __init__(self, db_service):
        """
        Initialize the apartment service.

        Args:
            db_service (DatabaseService): Database service
        """
        self.db_service = db_service

    def create(self, guesthouse_id, name):
        """
        Create a new apartment.

        Args:
            guesthouse_id (str): ID of the guest house
            name (str): Name of the apartment

        Returns:
            str or None: ID of the created apartment, or None if the name is already taken
        """
        session = self.db_service.get_session()
        try:
            # Check if apartment with the same name already exists
            existing = session.query(Apartment).filter(
                Apartment.guesthouse_id == guesthouse_id,
                Apartment.name == name
            ).first()

            if existing:
                return None

            # Check if the guest house exists
            guesthouse = session.query(GuestHouse).filter(GuestHouse.id == guesthouse_id).first()
            if not guesthouse:
                return None

            # Count existing apartments to enforce the limit
            apartment_count = session.query(Apartment).filter(
                Apartment.guesthouse_id == guesthouse_id
            ).count()

            if apartment_count >= 10:
                return None

            # Create new apartment
            apartment = Apartment(name=name)
            apartment.guesthouse_id = guesthouse_id

            session.add(apartment)
            session.commit()

            return apartment.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get(self, apartment_id):
        """
        Get an apartment by ID.

        Args:
            apartment_id (str): ID of the apartment

        Returns:
            Apartment or None: The apartment if found, None otherwise
        """
        session = self.db_service.get_session()
        try:
            apartment = session.query(Apartment).filter(Apartment.id == apartment_id).first()
            return apartment
        finally:
            session.close()

    def get_by_name(self, guesthouse_id, name):
        """
        Get an apartment by name.

        Args:
            guesthouse_id (str): ID of the guest house
            name (str): Name of the apartment

        Returns:
            Apartment or None: The apartment if found, None otherwise
        """
        session = self.db_service.get_session()
        try:
            apartment = session.query(Apartment).filter(
                Apartment.guesthouse_id == guesthouse_id,
                Apartment.name == name
            ).first()
            return apartment
        finally:
            session.close()

    def update(self, apartment_id, name):
        """
        Update an apartment.

        Args:
            apartment_id (str): ID of the apartment to update
            name (str): New name for the apartment

        Returns:
            bool: True if updated successfully, False otherwise
        """
        session = self.db_service.get_session()
        try:
            apartment = session.query(Apartment).filter(Apartment.id == apartment_id).first()
            if not apartment:
                return False

            # Check if the new name is already taken by another apartment
            existing = session.query(Apartment).filter(
                Apartment.guesthouse_id == apartment.guesthouse_id,
                Apartment.name == name,
                Apartment.id != apartment_id
            ).first()

            if existing:
                return False

            apartment.name = name
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, apartment_id):
        """
        Delete an apartment.

        Args:
            apartment_id (str): ID of the apartment to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        session = self.db_service.get_session()
        try:
            apartment = session.query(Apartment).filter(Apartment.id == apartment_id).first()
            if not apartment:
                return False

            session.delete(apartment)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()