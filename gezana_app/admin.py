from django.contrib import admin
from .models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_vegetarian")
    list_filter = ("category", "is_vegetarian")
    search_fields = ("name", "description")

from .models import Table, Booking

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("table_number", "capacity")
    list_filter = ("capacity",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "time", "guests", "table")
    list_filter = ("date", "time", "table")
