from datetime import datetime, timedelta
from .models import Booking, Table

BOOKING_DURATION = 90  # minutes


def find_available_table(date, time, guests, exclude_booking_id=None):

    suitable_tables = Table.objects.filter(capacity__gte=guests).order_by("capacity")

    requested_start = datetime.combine(date, time)
    requested_end = requested_start + timedelta(minutes=BOOKING_DURATION)

    for table in suitable_tables:

        existing_bookings = Booking.objects.filter(date=date, table=table)

        if exclude_booking_id:
            existing_bookings = existing_bookings.exclude(id=exclude_booking_id)

        conflict = False

        for booking in existing_bookings:
            existing_start = datetime.combine(date, booking.time)
            existing_end = existing_start + timedelta(minutes=BOOKING_DURATION)

            if requested_start < existing_end and existing_start < requested_end:
                conflict = True
                break

        if not conflict:
            return table

    return None