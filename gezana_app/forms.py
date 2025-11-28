from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date, time
from .models import Booking, Table
from .utils import find_available_table

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["name", "email", "phone", "guests", "date", "time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "name": "Full name",
            "email": "Email address",
            "phone": "Phone number (optional)",
            "guests": "Number of guests",
            "date": "Booking date",
            "time": "Booking time",
        }
        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("placeholder", placeholders.get(field_name, ""))
            field.widget.attrs.setdefault("class", "input-with-icon")

        # Use browser date picker
        if "date" in self.fields:
            self.fields["date"].widget.input_type = "date"

    def clean_date(self):
        booking_date = self.cleaned_data["date"]

        if booking_date < date.today():
            raise forms.ValidationError("You cannot book a date in the past.")

        return booking_date

    def clean_time(self):
        booking_time = self.cleaned_data["time"]

        # Restaurant hours: 12:00 PM to 7:00 PM inclusive
        start = time(hour=12, minute=0)
        end = time(hour=19, minute=0)
        if booking_time < start or booking_time > end:
            raise forms.ValidationError("Bookings must be between 12:00 PM and 7:00 PM.")

        return booking_time

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("date")
        booking_time = cleaned_data.get("time")
        guests = cleaned_data.get("guests")
        email = cleaned_data.get("email")
        phone = cleaned_data.get("phone")

        # Only run availability checks when required fields are present.
        if not booking_date or not booking_time or not guests:
            return cleaned_data

        # Ensure there is at least one table that can seat this party size.
        suitable_tables = Table.objects.filter(capacity__gte=guests)
        if not suitable_tables.exists():
            raise ValidationError("No tables can accommodate that party size. Please reduce guests or contact us.")

        # Check availability at the requested slot.
        table = find_available_table(booking_date, booking_time, guests)
        if table is None:
            raise ValidationError("We are fully booked for that date and time. Please choose another slot.")

        # Prevent duplicate bookings by same contact on the same date.
        if email or phone:
            dup_q = Q(date=booking_date)
            if email:
                dup_q &= Q(email__iexact=email)
            if phone:
                dup_q |= Q(date=booking_date, phone__iexact=phone)
            existing = Booking.objects.filter(dup_q)
            if existing.exists():
                raise ValidationError("It looks like you already have a booking for that date. Please modify the existing booking or choose another date.")

        # store selected table so view can reuse without re-querying
        self.available_table = table

        return cleaned_data
class CancelBookingForm(forms.Form):
    reference = forms.CharField(max_length=8)
