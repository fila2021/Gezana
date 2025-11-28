from .models import MenuItem
from django.shortcuts import get_object_or_404
from django.shortcuts import render

def home(request):
    return render(request, 'gezana_app/home.html')

def menu_list(request):
    items = MenuItem.objects.all()
    return render(request, "gezana_app/menu_list.html", {"items": items})

def menu_detail(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    return render(request, "gezana_app/menu_detail.html", {"item": item})

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import BookingForm
from .utils import find_available_table
from .models import Booking

def make_booking(request):
    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)

            table = find_available_table(
                booking.date,
                booking.time,
                booking.guests
            )

            if table is None:
                messages.error(request, "Sorry, no table is available at that time.")
            else:
                booking.table = table
                booking.save()
                messages.success(request, "Your booking has been confirmed!")
                return redirect("gezana_app:booking_success")

    else:
        form = BookingForm()

    return render(request, "gezana_app/booking_form.html", {"form": form})



def booking_success(request):
    last_booking = Booking.objects.last()
    return render(request, "gezana_app/booking_success.html", {"booking": last_booking})

from .forms import CancelBookingForm

def cancel_booking(request):
    if request.method == "POST":
        form = CancelBookingForm(request.POST)
        if form.is_valid():
            ref = form.cleaned_data["reference"].strip().upper()

            try:
                booking = Booking.objects.get(reference=ref)
                booking.delete()
                messages.success(request, "Your booking has been cancelled.")
                return redirect("gezana_app:home")
            except Booking.DoesNotExist:
                messages.error(request, "Invalid cancellation code.")
    else:
        form = CancelBookingForm()

    return render(request, "gezana_app/cancel_booking.html", {"form": form})
