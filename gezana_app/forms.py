from django import forms
from datetime import date
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

    def clean_date(self):
        booking_date = self.cleaned_data["date"]

        if booking_date < date.today():
            raise forms.ValidationError("You cannot book a date in the past.")

        return booking_date

    def clean_time(self):
        booking_time = self.cleaned_data["time"]

        # Restaurant hours (customize later)
        if booking_time < forms.TimeField().to_python("12:00") or booking_time > forms.TimeField().to_python("23:00"):
            raise forms.ValidationError("Bookings must be between 12 PM and 11 PM.")

        return booking_time
class CancelBookingForm(forms.Form):
    reference = forms.CharField(max_length=8)
