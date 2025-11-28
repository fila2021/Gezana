from django.urls import path
from . import views

app_name = 'gezana_app'

urlpatterns = [
    path("", views.home, name="home"),
    path("menu/", views.menu_list, name="menu_list"),
    path("menu/<int:pk>/", views.menu_detail, name="menu_detail"),
    path("book/", views.make_booking, name="make_booking"),
    path("booking-success/", views.booking_success, name="booking_success"),
]

