from reservation.models import Reservation

class ReservationService:
    """Service for reservation operations."""

    def __init__(self, db_service):
        """
        Initialize the reservation service.

        Args:
            db_service (DatabaseService): Database service
        """
        self.db_service = db_service

    def create(self, apartment_id, check_in_date, check_out_date, num_guests,
               contact_name, contact_number, contact_email, booking_mode, notes=""):
        """
        Create a new reservation.

        Args:
            apartment_id (str): ID of the apartment
            check_in_date (datetime): Date of check-in
            check_out_date (datetime): Date of check-out
            num_guests (int): Number of guests
            contact_name (str): Name of the contact person
            contact_number (str): Contact phone number
            contact_email (str): Contact email address
            booking_mode (str): How the booking was made
            notes (str, optional): Additional notes

        Returns:
            str or None: ID of the created reservation, or None if there was a conflict
        """
        session = self.db_service.get_session()
        try:
            # Check for date conflicts
            conflicts = session.query(Reservation).filter(
                Reservation.apartment_id == apartment_id,
                Reservation.check_out_date > check_in_date,
                Reservation.check_in_date < check_out_date
            ).count()

            if conflicts > 0:
                session.close()
                return None

            # Create new reservation
            reservation = Reservation(
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                num_guests=num_guests,
                contact_name=contact_name,
                contact_number=contact_number,
                contact_email=contact_email,
                booking_mode=booking_mode,
                notes=notes
            )
            reservation.apartment_id = apartment_id

            session.add(reservation)
            session.commit()

            return reservation.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get(self, reservation_id):
        """
        Get a reservation by ID.

        Args:
            reservation_id (str): ID of the reservation

        Returns:
            Reservation or None: The reservation if found, None otherwise
        """
        session = self.db_service.get_session()
        try:
            reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
            return reservation
        finally:
            session.close()

    def update(self, reservation_id, **kwargs):
        """
        Update a reservation.

        Args:
            reservation_id (str): ID of the reservation to update
            **kwargs: Fields to update

        Returns:
            bool: True if updated successfully, False otherwise
        """
        session = self.db_service.get_session()
        try:
            reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
            if not reservation:
                return False

            # Check for date conflicts if dates are being updated
            if 'check_in_date' in kwargs or 'check_out_date' in kwargs:
                check_in_date = kwargs.get('check_in_date', reservation.check_in_date)
                check_out_date = kwargs.get('check_out_date', reservation.check_out_date)

                conflicts = session.query(Reservation).filter(
                    Reservation.apartment_id == reservation.apartment_id,
                    Reservation.id != reservation_id,
                    Reservation.check_out_date > check_in_date,
                    Reservation.check_in_date < check_out_date
                ).count()

                if conflicts > 0:
                    return False

            # Update fields
            for key, value in kwargs.items():
                if hasattr(reservation, key):
                    setattr(reservation, key, value)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, reservation_id):
        """
        Delete a reservation.

        Args:
            reservation_id (str): ID of the reservation to delete

        Returns:
            bool: True if deleted, False if not found
        """
        session = self.db_service.get_session()
        try:
            reservation = session.query(Reservation).filter(Reservation.id == reservation_id).first()
            if not reservation:
                return False

            session.delete(reservation)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_by_apartment(self, apartment_id):
        """
        Get all reservations for an apartment.

        Args:
            apartment_id (str): ID of the apartment

        Returns:
            list: List of reservations
        """
        session = self.db_service.get_session()
        try:
            reservations = session.query(Reservation).filter(
                Reservation.apartment_id == apartment_id
            ).all()
            return reservations
        finally:
            session.close()

    def find_available_dates(self, apartment_id, start_date, end_date):
        """
        Find available date ranges for an apartment.

        Args:
            apartment_id (str): ID of the apartment
            start_date (datetime): Start of the date range to check
            end_date (datetime): End of the date range to check

        Returns:
            list: List of (start_date, end_date) tuples representing available periods
        """
        session = self.db_service.get_session()
        try:
            # Get all reservations for this apartment in the date range
            reservations = session.query(Reservation).filter(
                Reservation.apartment_id == apartment_id,
                Reservation.check_out_date > start_date,
                Reservation.check_in_date < end_date
            ).order_by(Reservation.check_in_date).all()

            # If no reservations, the entire range is available
            if not reservations:
                return [(start_date, end_date)]

            # Find available periods
            available_periods = []
            current_date = start_date

            for res in reservations:
                # If there's a gap before this reservation, add it
                if current_date < res.check_in_date:
                    available_periods.append((current_date, res.check_in_date))

                # Move current_date to after this reservation
                current_date = max(current_date, res.check_out_date)

            # If there's a gap after the last reservation, add it
            if current_date < end_date:
                available_periods.append((current_date, end_date))

            return available_periods
        finally:
            session.close()