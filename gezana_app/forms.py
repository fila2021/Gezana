from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date, time

from .models import Booking, Table
from .utils import find_available_table


class BookingForm(forms.ModelForm):
    # Restaurant hours: 12:00 to 19:00 inclusive (last slot at 19:00)
    OPEN_TIME = time(12, 0)
    CLOSE_TIME = time(19, 0)

    # ✅ Dropdown time choices every 30 mins
    TIME_CHOICES = [
        (time(h, m).strftime("%H:%M"), time(h, m).strftime("%H:%M"))
        for h in range(12, 20)  # 12..19
        for m in (0, 30)
    ]

    # Override the model TimeField widget as a dropdown
    time = forms.ChoiceField(choices=TIME_CHOICES)

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

        # ✅ Use browser date picker + prevent selecting past dates in UI
        if "date" in self.fields:
            self.fields["date"].widget.input_type = "date"
            self.fields["date"].widget.attrs["min"] = date.today().isoformat()

    def clean_date(self):
        booking_date = self.cleaned_data["date"]
        if booking_date < date.today():
            raise forms.ValidationError("❌ You cannot book a date in the past.")
        return booking_date

    def clean_time(self):
        """
        Our time field is now a ChoiceField returning a string ("HH:MM"),
        so we convert it to a datetime.time to match the Booking model.
        """
        booking_time_str = self.cleaned_data["time"]  # e.g. "12:30"
        hour, minute = map(int, booking_time_str.split(":"))
        booking_time = time(hour=hour, minute=minute)

        if booking_time < self.OPEN_TIME or booking_time > self.CLOSE_TIME:
            raise forms.ValidationError("❌ Bookings must be between 12:00 and 19:00.")

        return booking_time

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("date")
        booking_time = cleaned_data.get("time")
        guests = cleaned_data.get("guests")
        email = cleaned_data.get("email")
        phone = cleaned_data.get("phone")

        if not booking_date or not booking_time or not guests:
            return cleaned_data

        suitable_tables = Table.objects.filter(capacity__gte=guests)
        if not suitable_tables.exists():
            raise ValidationError(
                "No tables can accommodate that party size. Please reduce guests or contact us."
            )

        table = find_available_table(booking_date, booking_time, guests)
        if table is None:
            raise ValidationError(
                "We are fully booked for that date and time. Please choose another slot."
            )

        # Prevent duplicate bookings by same contact on the same date.
        if email or phone:
            dup_q = Q(date=booking_date)
            if email:
                dup_q &= Q(email__iexact=email)
            if phone:
                dup_q |= Q(date=booking_date, phone__iexact=phone)

            if Booking.objects.filter(dup_q).exists():
                raise ValidationError(
                    "It looks like you already have a booking for that date. "
                    "Please modify the existing booking or choose another date."
                )

        self.available_table = table
        return cleaned_data


class CancelBookingForm(forms.Form):
    reference = forms.CharField(max_length=8)
