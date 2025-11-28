from django import forms
from datetime import date
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["name", "email", "phone", "guests", "date", "time"]

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
