from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import date, time, datetime
import re

from .models import Booking, Table
from .utils import find_available_table


PHONE_REGEX = re.compile(r'^\+?[0-9\s\-\(\)]{7,20}$')


class BookingForm(forms.ModelForm):
    OPEN_TIME = time(12, 0)
    CLOSE_TIME = time(19, 0)

    # ✅ Time dropdown: 12:00 → 19:00 (30 min steps)
    TIME_CHOICES = []
    _current = datetime.combine(date.today(), OPEN_TIME)
    _end = datetime.combine(date.today(), CLOSE_TIME)

    while _current <= _end:
        label = _current.strftime("%H:%M")
        TIME_CHOICES.append((label, label))
        _current = (
            _current.replace(minute=30)
            if _current.minute == 0
            else _current.replace(hour=_current.hour + 1, minute=0)
        )

    time = forms.ChoiceField(choices=TIME_CHOICES)

    class Meta:
        model = Booking
        fields = ["name", "email", "phone", "guests", "date", "time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            "name": "Full name",
            "email": "Email address (recommended)",
            "phone": "Phone number (optional)",
            "guests": "Number of guests",
            "date": "Booking date",
            "time": "Booking time",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("placeholder", placeholders.get(field_name, ""))
            field.widget.attrs.setdefault("class", "input-with-icon")

        # Email optional (since phone exists)
        self.fields["email"].required = False

        # Date picker + UI restriction
        self.fields["date"].widget.input_type = "date"
        self.fields["date"].widget.attrs["min"] = date.today().isoformat()

    # -------------------
    # FIELD VALIDATIONS
    # -------------------

    def clean_date(self):
        booking_date = self.cleaned_data.get("date")
        if booking_date and booking_date < date.today():
            raise ValidationError("❌ You cannot book a date in the past.")
        return booking_date

    def clean_time(self):
        time_str = self.cleaned_data.get("time")
        if not time_str:
            return time_str

        hour, minute = map(int, time_str.split(":"))
        booking_time = time(hour=hour, minute=minute)

        if booking_time < self.OPEN_TIME or booking_time > self.CLOSE_TIME:
            raise ValidationError("❌ Bookings must be between 12:00 and 19:00.")

        return booking_time

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if not phone:
            return phone  # optional

        if not PHONE_REGEX.match(phone):
            raise ValidationError(
                "❌ Enter a valid phone number (digits, spaces, +, -, or parentheses)."
            )

        # Normalize phone (keep digits + leading +)
        cleaned = re.sub(r"[^\d+]", "", phone)

        # Length check (E.164-ish)
        digits_only = re.sub(r"\D", "", cleaned)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValidationError("❌ Phone number must contain 7–15 digits.")

        return cleaned

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("date")
        booking_time = cleaned_data.get("time")
        guests = cleaned_data.get("guests")
        email = cleaned_data.get("email")
        phone = cleaned_data.get("phone")

        if not booking_date or not booking_time or not guests:
            return cleaned_data

        # Require at least one contact method
        if not email and not phone:
            raise ValidationError(
                "Please provide at least an email address or a phone number."
            )

        # Capacity check
        if not Table.objects.filter(capacity__gte=guests).exists():
            raise ValidationError(
                "No tables can accommodate that party size. Please reduce guests."
            )

        # Availability check
        table = find_available_table(booking_date, booking_time, guests)
        if table is None:
            raise ValidationError(
                "We are fully booked for that date and time. Please choose another slot."
            )

        # Duplicate booking check (correct logic)
        dup_q = Q()
        if email:
            dup_q |= Q(date=booking_date, email__iexact=email)
        if phone:
            dup_q |= Q(date=booking_date, phone__iexact=phone)

        if Booking.objects.filter(dup_q).exists():
            raise ValidationError(
                "It looks like you already have a booking for that date."
            )

        self.available_table = table
        return cleaned_data
