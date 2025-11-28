from .models import Table, Booking

def find_available_table(date, time, guests):
    """
    Returns a table that fits the number of guests and is not booked
    for the given date + time.
    """

    # Get all tables that can seat at least the number of guests
    suitable_tables = Table.objects.filter(capacity__gte=guests).order_by("capacity")

    for table in suitable_tables:
        conflict = Booking.objects.filter(
            date=date,
            time=time,
            table=table
        ).exists()

        if not conflict:
            return table

    return None
