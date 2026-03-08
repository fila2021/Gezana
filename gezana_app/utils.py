from datetime import datetime, timedelta

from .models import Booking, Table

BOOKING_DURATION_MINUTES = 90
BUFFER_MINUTES = 0


def _overlaps(start_a, end_a, start_b, end_b):
    """Return True if two booking windows overlap."""
    return start_a < end_b and start_b < end_a


def find_available_table(
    booking_date,
    booking_time,
    guests,
    exclude_booking_id=None,
):
    """Return the smallest suitable available table for the requested slot."""
    suitable_tables = Table.objects.filter(capacity__gte=guests).order_by("capacity")

    requested_start = datetime.combine(booking_date, booking_time)
    requested_end = requested_start + timedelta(
        minutes=BOOKING_DURATION_MINUTES + BUFFER_MINUTES
    )

    for table in suitable_tables:
        existing_bookings = Booking.objects.filter(
            date=booking_date,
            table=table,
        ).only("id", "time")

        if exclude_booking_id:
            existing_bookings = existing_bookings.exclude(pk=exclude_booking_id)

        conflict = False

        for booking in existing_bookings:
            existing_start = datetime.combine(booking_date, booking.time)
            existing_end = existing_start + timedelta(
                minutes=BOOKING_DURATION_MINUTES + BUFFER_MINUTES
            )

            if _overlaps(
                requested_start,
                requested_end,
                existing_start,
                existing_end,
            ):
                conflict = True
                break

        if not conflict:
            return table

    return None