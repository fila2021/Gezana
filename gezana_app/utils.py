from datetime import datetime, timedelta
from .models import Table, Booking

BOOKING_DURATION_MINUTES = 90   # table occupied duration
BUFFER_MINUTES = 0              # optional buffer between bookings


def _overlaps(start_a, end_a, start_b, end_b):
    """Return True if [start_a, end_a) overlaps [start_b, end_b)."""
    return start_a < end_b and start_b < end_a


def find_available_table(booking_date, booking_time, guests):
    """
    Returns the smallest suitable table that does NOT overlap with
    existing bookings on the same date.
    """
    suitable_tables = (
        Table.objects
        .filter(capacity__gte=guests)
        .order_by("capacity")
    )

    requested_start = datetime.combine(booking_date, booking_time)
    requested_end = requested_start + timedelta(minutes=BOOKING_DURATION_MINUTES + BUFFER_MINUTES)

    for table in suitable_tables:
        existing = (
            Booking.objects
            .filter(date=booking_date, table=table)
            .only("time")
        )

        conflict = False
        for b in existing:
            existing_start = datetime.combine(booking_date, b.time)
            existing_end = existing_start + timedelta(minutes=BOOKING_DURATION_MINUTES + BUFFER_MINUTES)

            if _overlaps(requested_start, requested_end, existing_start, existing_end):
                conflict = True
                break

        if not conflict:
            return table

    return None
