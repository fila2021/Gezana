from django import forms
from datetime import date, time
from .models import Booking

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
class CancelBookingForm(forms.Form):
    reference = forms.CharField(max_length=8)
