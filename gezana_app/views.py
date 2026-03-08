from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingForm, BookingLookupForm, CancelBookingForm
from .models import Booking, MenuItem
from .utils import find_available_table


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
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(ingredients__icontains=search)
        )

    recommended = None
    if not category and not search:
        recommended = (
            MenuItem.objects.filter(
                Q(is_chef_choice=True) | Q(is_popular=True) | Q(is_new=True)
            )
            .order_by("-is_chef_choice", "-is_popular", "-is_new")[:3]
        )

    return render(
        request,
        "gezana_app/menu_list.html",
        {
            "items": items,
            "recommended": recommended,
            "category": category,
            "search": search,
        },
    )


def menu_detail(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)

    recommended = (
        MenuItem.objects.filter(category=item.category)
        .exclude(pk=item.pk)
        .order_by("-is_chef_choice", "-is_popular", "-is_new", "name")[:6]
    )

    if not recommended:
        recommended = (
            MenuItem.objects.exclude(pk=item.pk)
            .filter(Q(is_chef_choice=True) | Q(is_popular=True) | Q(is_new=True))
            .order_by("-is_chef_choice", "-is_popular", "-is_new", "name")[:6]
        )

    return render(
        request,
        "gezana_app/menu_detail.html",
        {
            "item": item,
            "recommended": recommended,
        },
    )


def make_booking(request):
    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            booking = form.save(commit=False)
            table = getattr(form, "available_table", None)

            if table is None:
                table = find_available_table(
                    booking.date,
                    booking.time,
                    booking.guests,
                )

            if table is None:
                messages.error(request, "Sorry, no table is available at that time.")
                return render(request, "gezana_app/booking_form.html", {"form": form})

            booking.table = table
            booking.save()

            _send_booking_confirmation(booking)
            request.session["last_booking_reference"] = booking.reference
            messages.success(request, "Your booking has been confirmed.")
            return redirect("gezana_app:booking_success")

        messages.warning(request, "Please correct the highlighted fields and try again.")

    else:
        form = BookingForm()

    return render(request, "gezana_app/booking_form.html", {"form": form})


def booking_success(request):
    reference = request.session.pop("last_booking_reference", None)
    booking = Booking.objects.filter(reference=reference).first() if reference else None

    if not booking:
        messages.info(
            request,
            "Your booking is confirmed. If you need your reference, please check your email.",
        )
        return redirect("gezana_app:make_booking")

    return render(request, "gezana_app/booking_success.html", {"booking": booking})


def manage_booking(request):
    form = BookingLookupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        reference = form.cleaned_data["reference"]
        email = (form.cleaned_data.get("email") or "").strip()
        phone = (form.cleaned_data.get("phone") or "").strip()

        filters = Q(reference=reference)
        if email:
            filters &= Q(email__iexact=email)
        elif phone:
            filters &= Q(phone=phone)

        booking = Booking.objects.filter(filters).first()

        if booking:
            return redirect("gezana_app:booking_detail", reference=booking.reference)

        messages.error(
            request,
            "We could not find a booking matching those details. Please try again.",
        )

    return render(request, "gezana_app/manage_booking.html", {"form": form})


def booking_detail(request, reference):
    booking = get_object_or_404(Booking, reference=reference.upper())
    return render(request, "gezana_app/booking_detail.html", {"booking": booking})


def edit_booking(request, reference):
    booking = get_object_or_404(Booking, reference=reference.upper())

    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)

        if form.is_valid():
            updated_booking = form.save(commit=False)
            table = getattr(form, "available_table", None)

            if table is None:
                table = find_available_table(
                    updated_booking.date,
                    updated_booking.time,
                    updated_booking.guests,
                    exclude_booking_id=booking.pk,
                )

            if table is None:
                messages.error(request, "Sorry, no table is available at that time.")
                return render(
                    request,
                    "gezana_app/edit_booking.html",
                    {"form": form, "booking": booking},
                )

            updated_booking.table = table
            updated_booking.save()

            messages.success(request, "Your booking has been updated successfully.")
            return redirect(
                "gezana_app:booking_detail",
                reference=updated_booking.reference,
            )

        messages.warning(request, "Please correct the highlighted fields and try again.")
    else:
        form = BookingForm(instance=booking)

    return render(
        request,
        "gezana_app/edit_booking.html",
        {"form": form, "booking": booking},
    )


def cancel_booking(request):
    if request.method == "POST":
        form = CancelBookingForm(request.POST)

        if form.is_valid():
            reference = form.cleaned_data["reference"]

            try:
                booking = Booking.objects.get(reference=reference)
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
    if not booking.email:
        return

    subject = "Your Gezana booking is confirmed"
    text_body = (
        f"Hi {booking.name},\n\n"
        f"Your table is booked for {booking.date} at {booking.time}.\n"
        f"Guests: {booking.guests}\n"
        f"Reference: {booking.reference}\n\n"
        "Thank you for choosing Gezana Restaurant."
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; color: #2d1d16;">
      <h2 style="color:#8c3c1c;">Gezana Booking Confirmed</h2>
      <p>Hi {booking.name},</p>
      <p>Your booking has been confirmed.</p>
      <ul style="list-style:none; padding:0;">
        <li><strong>Date:</strong> {booking.date}</li>
        <li><strong>Time:</strong> {booking.time}</li>
        <li><strong>Guests:</strong> {booking.guests}</li>
        <li><strong>Reference:</strong> {booking.reference}</li>
      </ul>
      <p>Thank you for choosing Gezana.</p>
    </div>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)


def _send_cancellation_confirmation(booking):
    if not booking.email:
        return

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
      <p>We hope to see you soon.</p>
    </div>
    """

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=True)
    