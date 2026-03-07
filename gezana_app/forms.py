from datetime import date, datetime, time, timedelta
import re

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from .models import Booking, Table
from .utils import find_available_table

PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")


class BookingForm(forms.ModelForm):
    OPEN_TIME = time(12, 0)
    CLOSE_TIME = time(19, 0)
    LEAD_TIME_MINUTES = 0

    TIME_CHOICES = []
    _cur = datetime.combine(date.today(), OPEN_TIME)
    _end = datetime.combine(date.today(), CLOSE_TIME)
    while _cur <= _end:
        slot = _cur.strftime("%H:%M")
        TIME_CHOICES.append((slot, slot))
        _cur += timedelta(minutes=30)

    time = forms.ChoiceField(choices=TIME_CHOICES)

    class Meta:
        model = Booking
        fields = ["name", "email", "phone", "guests", "date", "time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            field.widget.attrs.setdefault(
                "placeholder", placeholders.get(field_name, "")
            )
            field.widget.attrs.setdefault("class", "input-with-icon")

        self.fields["date"].widget.input_type = "date"
        self.fields["date"].widget.attrs["min"] = date.today().isoformat()

        if self.instance and self.instance.pk and self.instance.time:
            self.initial.setdefault("time", self.instance.time.strftime("%H:%M"))

    def clean_date(self):
        booking_date = self.cleaned_data.get("date")
        if booking_date and booking_date < date.today():
            raise ValidationError(
                "Date is invalid: you cannot book a date in the past."
            )
        return booking_date

    def clean_time(self):
        raw_time = self.cleaned_data.get("time")
        if not raw_time:
            return raw_time

        hours, minutes = map(int, raw_time.split(":"))
        booking_time = time(hours, minutes)

        if minutes not in (0, 30):
            raise ValidationError(
                "Please choose a valid time slot every 30 minutes."
            )

        if booking_time < self.OPEN_TIME or booking_time > self.CLOSE_TIME:
            raise ValidationError(
                "Bookings are only available from 12:00 to 19:00."
            )

        return booking_time

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return phone

        if not PHONE_REGEX.match(phone):
            raise ValidationError("Enter a valid phone number.")

        cleaned_phone = re.sub(r"[^\d+]", "", phone)
        digits_only = re.sub(r"\D", "", cleaned_phone)

        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValidationError("Phone number must contain 7 to 15 digits.")

        return cleaned_phone

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get("date")
        booking_time = cleaned_data.get("time")
        guests = cleaned_data.get("guests")
        email = (cleaned_data.get("email") or "").strip()
        phone = (self.cleaned_data.get("phone") or "").strip()

        if not booking_date or not booking_time or not guests:
            return cleaned_data

        if not email and not phone:
            raise ValidationError(
                "Please provide at least an email address or phone number."
            )

        now_local = timezone.localtime(timezone.now())
        current_timezone = timezone.get_current_timezone()
        requested_dt = timezone.make_aware(
            datetime.combine(booking_date, booking_time),
            current_timezone,
        )
        min_allowed = now_local + timedelta(minutes=self.LEAD_TIME_MINUTES)

        if booking_date == now_local.date() and requested_dt <= min_allowed:
            raise ValidationError("Please choose a future time for today.")

        if not Table.objects.filter(capacity__gte=guests).exists():
            raise ValidationError(
                "No tables can accommodate that party size. Please reduce guests."
            )

        exclude_booking_id = (
            self.instance.pk if self.instance and self.instance.pk else None
        )

        table = find_available_table(
            booking_date,
            booking_time,
            guests,
            exclude_booking_id=exclude_booking_id,
        )

        if table is None:
            raise ValidationError(
                "We are fully booked for that date and time. Please choose another slot."
            )

        duplicate_query = Booking.objects.all()
        if exclude_booking_id:
            duplicate_query = duplicate_query.exclude(pk=exclude_booking_id)

        duplicate_filter = Q()
        if email:
            duplicate_filter |= Q(date=booking_date, email__iexact=email)
        if phone:
            duplicate_filter |= Q(date=booking_date, phone__iexact=phone)

        if duplicate_filter and duplicate_query.filter(duplicate_filter).exists():
            raise ValidationError(
                "It looks like you already have a booking for that date."
            )

        self.available_table = table
        return cleaned_data


class CancelBookingForm(forms.Form):
    reference = forms.CharField(max_length=8)

    def clean_reference(self):
        return self.cleaned_data["reference"].strip().upper()


class BookingLookupForm(forms.Form):
    reference = forms.CharField(max_length=8)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=20, required=False)

    def clean_reference(self):
        return self.cleaned_data["reference"].strip().upper()

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return phone

        if not PHONE_REGEX.match(phone):
            raise ValidationError("Enter a valid phone number.")

        return re.sub(r"[^\d+]", "", phone)

    def clean(self):
        cleaned_data = super().clean()
        email = (cleaned_data.get("email") or "").strip()
        phone = (cleaned_data.get("phone") or "").strip()

        if not email and not phone:
            raise ValidationError(
                "Provide the booking reference and either email or phone."
            )

        return cleaned_data