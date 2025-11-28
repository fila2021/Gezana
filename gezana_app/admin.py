from django.contrib import admin
from .models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_vegetarian")
    list_filter = ("category", "is_vegetarian")
    search_fields = ("name", "description")
