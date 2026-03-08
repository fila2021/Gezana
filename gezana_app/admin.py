from django.contrib import admin

from .models import Booking, MenuItem, Table


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "is_vegetarian",
        "is_popular",
        "is_new",
        "is_chef_choice",
    )
    list_filter = (
        "category",
        "is_vegetarian",
        "is_popular",
        "is_new",
        "is_chef_choice",
    )
    search_fields = ("name", "description", "ingredients")


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("table_number", "capacity")
    search_fields = ("table_number",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "time", "guests", "reference", "table")
    list_filter = ("date", "time", "table")
    search_fields = ("name", "email", "phone", "reference")