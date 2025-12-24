from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Q


from .forms import BookingForm, CancelBookingForm
from .utils import find_available_table
from .models import Booking, MenuItem


def home(request):
    return render(request, "gezana_app/home.html")


def about(request):
    return render(request, "gezana_app/about.html")


def contact(request):
    return render(request, "gezana_app/contact.html")



def menu_list(request):
    category = request.GET.get("category")
    search = request.GET.get("search")

    items = MenuItem.objects.all()

    if category:
        items = items.filter(category=category)

    if search:
        items = items.filter(
            Q(name__icontains=search) | Q(ingredients__icontains=search)
        )

    # Recommended (top picks) — show even when filters are used
    recommended = (
        MenuItem.objects
        .filter(Q(is_chef_choice=True) | Q(is_popular=True) | Q(is_new=True))
        .order_by("-is_chef_choice", "-is_popular", "-is_new", "name")[:6]
    )

    return render(request, "gezana_app/menu_list.html", {
        "items": items,
        "recommended": recommended,
        "category": category,
        "search": search,
    })





def menu_detail(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)

    # Recommended items: same category, exclude current
    recommended = (
        MenuItem.objects
        .filter(category=item.category)
        .exclude(pk=item.pk)
        .order_by("-is_chef_choice", "-is_popular", "-is_new", "name")[:6]
    )

    # fallback if category has few items (optional)
    if not recommended:
        recommended = (
            MenuItem.objects
            .exclude(pk=item.pk)
            .filter(Q(is_chef_choice=True) | Q(is_popular=True) | Q(is_new=True))
            .order_by("-is_chef_choice", "-is_popular", "-is_new", "name")[:6]
        )

    return render(request, "gezana_app/menu_detail.html", {
        "item": item,
        "recommended": recommended,
    })





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

        messages.warning(request, "Please correct the highlighted fields and try again.")

    else:
        form = BookingForm()

    return render(request, "gezana_app/booking_form.html", {"form": form})


def booking_success(request):
    ref = request.session.pop("last_booking_reference", None)
    booking = Booking.objects.filter(reference=ref).first() if ref else None

    if not booking:
        messages.info(
            request,
            "Your booking is confirmed. If you need your reference, please check your email."
        )
        return redirect("gezana_app:make_booking")

    return render(request, "gezana_app/booking_success.html", {"booking": booking})


def cancel_booking(request):
    if request.method == "POST":
        form = CancelBookingForm(request.POST)
        if form.is_valid():
            ref = form.cleaned_data["reference"].strip().upper()

            try:
                booking = Booking.objects.get(reference=ref)
                _send_cancellation_confirmation(booking)
                booking.delete()
                messages.success(request, "Your booking has been cancelled.")
                return redirect("gezana_app:home")
            except Booking.DoesNotExist:
                messages.error(request, "Invalid cancellation code.")
    else:
        form = CancelBookingForm()

    return render(request, "gezana_app/cancel_booking.html", {"form": form})


def _send_booking_confirmation(booking):
    subject = "Your Gezana booking is confirmed"
    text_body = (
        f"Hi {booking.name},\n\n"
        f"Your table is booked for {booking.date} at {booking.time}.\n"
        f"Guests: {booking.guests}\n"
        f"Reference: {booking.reference}\n"
        f"Table: {booking.table or 'Assigned on arrival'}\n\n"
        "If you need to cancel, use your reference code on the site.\n\n"
        "Gezana Restaurant"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; color: #2d1d16;">
      <h2 style="color:#8c3c1c;">Gezana Booking Confirmed</h2>
      <p>Hi {booking.name},</p>
      <p>Your table is booked. We look forward to hosting you.</p>
      <ul style="list-style:none; padding:0;">
        <li><strong>Date:</strong> {booking.date}</li>
        <li><strong>Time:</strong> {booking.time}</li>
        <li><strong>Guests:</strong> {booking.guests}</li>
        <li><strong>Reference:</strong> {booking.reference}</li>
        <li><strong>Table:</strong> {booking.table or 'Assigned on arrival'}</li>
      </ul>
      <p style="margin-top:10px;">Need to cancel? Enter your reference on the site.</p>
      <p style="color:#8c3c1c; font-weight:600;">Thank you for choosing Gezana.</p>
    </div>
    """

    recipient = [booking.email] if booking.email else []
    bcc = [settings.DEFAULT_FROM_EMAIL] if getattr(settings, "DEFAULT_FROM_EMAIL", None) else []

    # ✅ If phone-only booking, don't crash — just skip email
    if not recipient:
        return

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient,
        bcc=bcc,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)


def _send_cancellation_confirmation(booking):
    subject = "Your Gezana booking has been cancelled"
    text_body = (
        f"Hi {booking.name},\n\n"
        f"Your booking for {booking.date} at {booking.time} has been cancelled.\n"
        f"Reference: {booking.reference}\n\n"
        "We hope to welcome you another time.\n\n"
        "Gezana Restaurant"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; color: #2d1d16;">
      <h2 style="color:#8c3c1c;">Booking Cancelled</h2>
      <p>Hi {booking.name},</p>
      <p>Your booking has been cancelled.</p>
      <ul style="list-style:none; padding:0;">
        <li><strong>Date:</strong> {booking.date}</li>
        <li><strong>Time:</strong> {booking.time}</li>
        <li><strong>Guests:</strong> {booking.guests}</li>
        <li><strong>Reference:</strong> {booking.reference}</li>
      </ul>
      <p style="margin-top:10px;">If this was a mistake, please book again online.</p>
      <p style="color:#8c3c1c; font-weight:600;">We hope to see you soon.</p>
    </div>
    """

    recipient = [booking.email] if booking.email else []
    bcc = [settings.DEFAULT_FROM_EMAIL] if getattr(settings, "DEFAULT_FROM_EMAIL", None) else []

    if not recipient:
        return

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient,
        bcc=bcc,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)
