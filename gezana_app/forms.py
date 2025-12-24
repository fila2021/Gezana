from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from datetime import date, time, datetime, timedelta
import re

from .models import Booking, Table
from .utils import find_available_table

PHONE_REGEX = re.compile(r'^\+?[0-9\s\-\(\)]{7,20}$')


class BookingForm(forms.ModelForm):
    OPEN_TIME = time(12, 0)
    CLOSE_TIME = time(19, 0)

    # Optional buffer (e.g. 15 minutes)
    LEAD_TIME_MINUTES = 0

    # ✅ Time dropdown: 12:00 → 19:00 every 30 mins
    TIME_CHOICES = []
    _cur = datetime.combine(date.today(), OPEN_TIME)
    _end = datetime.combine(date.today(), CLOSE_TIME)
    while _cur <= _end:
        s = _cur.strftime("%H:%M")
        TIME_CHOICES.append((s, s))
        _cur += timedelta(minutes=30)

    time = forms.ChoiceField(choices=TIME_CHOICES)

    class Meta:
        model = Booking
        fields = ["name", "email", "phone", "guests", "date", "time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Email optional
        self.fields["email"].required = False

        placeholders = {
            "name": "Full name",
            "email": "Email address (optional)",
            "phone": "Phone number (optional)",
            "guests": "Number of guests",
            "date": "Booking date",
            "time": "Booking time",
        }

        for field_name, field in self.fields.items():
            field.widget.attrs.setdefault("placeholder", placeholders.get(field_name, ""))
            field.widget.attrs.setdefault("class", "input-with-icon")

        # Date picker + prevent past dates in UI
        self.fields["date"].widget.input_type = "date"
        self.fields["date"].widget.attrs["min"] = date.today().isoformat()

    def clean_date(self):
        d = self.cleaned_data.get("date")
        if d and d < date.today():
            raise ValidationError("❌ Date is invalid: you cannot book a date in the past.")
        return d

    def clean_time(self):
        t = self.cleaned_data.get("time")
        if not t:
            return t

        hh, mm = map(int, t.split(":"))
        booking_time = time(hh, mm)

        if mm not in (0, 30):
            raise ValidationError("❌ Please choose a valid time slot (every 30 minutes).")

        if booking_time < self.OPEN_TIME or booking_time > self.CLOSE_TIME:
            raise ValidationError("❌ Time is invalid: bookings are only available from 12:00 to 19:00.")

        return booking_time

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return phone

        if not PHONE_REGEX.match(phone):
            raise ValidationError("❌ Enter a valid phone number (digits, spaces, +, -, parentheses).")

        cleaned = re.sub(r"[^\d+]", "", phone)
        digits_only = re.sub(r"\D", "", cleaned)

        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValidationError("❌ Phone number must contain 7–15 digits.")

        return cleaned

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("date")
        booking_time = cleaned_data.get("time")
        guests = cleaned_data.get("guests")
        email = (cleaned_data.get("email") or "").strip()
        phone = (cleaned_data.get("phone") or "").strip()

        if not booking_date or not booking_time or not guests:
            return cleaned_data

        if not email and not phone:
            raise ValidationError("Please provide at least an email address or phone number.")

        # ✅ NEW: prevent booking a past time for today
        now_local = timezone.localtime(timezone.now())
        tz = timezone.get_current_timezone()
        requested_dt = timezone.make_aware(datetime.combine(booking_date, booking_time), tz)
        min_allowed = now_local + timedelta(minutes=self.LEAD_TIME_MINUTES)

        if booking_date == now_local.date() and requested_dt <= min_allowed:
            raise ValidationError("❌ Time is invalid: please choose a future time for today.")

        # capacity check
        if not Table.objects.filter(capacity__gte=guests).exists():
            raise ValidationError("No tables can accommodate that party size. Please reduce guests.")

        # availability check
        table = find_available_table(booking_date, booking_time, guests)
        if table is None:
            raise ValidationError("We are fully booked for that date and time. Please choose another slot.")

        # duplicate check
        dup_q = Q()
        if email:
            dup_q |= Q(date=booking_date, email__iexact=email)
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
