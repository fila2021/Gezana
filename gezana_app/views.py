from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Q

from .forms import BookingForm, CancelBookingForm
from .utils import find_available_table
from .models import Booking, MenuItem


def make_booking(request):
    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            booking = form.save(commit=False)

            table = getattr(form, "available_table", None)
            if table is None:
                table = find_available_table(booking.date, booking.time, booking.guests)

            if table is None:
                messages.error(request, "Sorry, no table is available at that time.")
                return render(request, "gezana_app/booking_form.html", {"form": form})

            booking.table = table
            booking.save()

            _send_booking_confirmation(booking)
            request.session["last_booking_reference"] = booking.reference
            messages.success(request, "Your booking has been confirmed!")
            return redirect("gezana_app:booking_success")

        # ✅ show a friendly warning if validation failed
        messages.warning(request, "Please correct the highlighted fields and try again.")

    else:
        form = BookingForm()

    return render(request, "gezana_app/booking_form.html", {"form": form})
