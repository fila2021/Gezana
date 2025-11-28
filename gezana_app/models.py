from django.db import models

class MenuCategory(models.TextChoices):
    APPETIZER = "Appetizer", "Appetizer"
    MAIN = "Main", "Main"
    SIDES = "Sides", "Sides"
    DESSERT = "Dessert", "Dessert"
    DRINK = "Drink", "Drink"

class MenuItem(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=20, choices=MenuCategory.choices, default=MenuCategory.MAIN)
    is_vegetarian = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category}) - €{self.price}"
from django.db import models
from django.utils import timezone
from datetime import time

class Table(models.Model):
    """
    Physical tables in the restaurant. 
    Example capacities: 2, 4, 6, 8.
    """
    table_number = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} seats)"


class Booking(models.Model):
    """
    Stores a booking request.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    guests = models.PositiveIntegerField()
    date = models.DateField()
    time = models.TimeField()
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.date} {self.time} ({self.guests} guests)"
