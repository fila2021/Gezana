from django.core.files import File
from pathlib import Path
from django.db import models
import random
import string


class MenuCategory(models.TextChoices):
    APPETIZER = "Appetizer", "Appetizer"
    MAIN = "Main", "Main"
    SIDES = "Sides", "Sides"
    DESSERT = "Dessert", "Dessert"
    DRINK = "Drink", "Drink"


class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ("starter", "Starter"),
        ("main", "Main Course"),
        ("side", "Side Dish"),
        ("dessert", "Dessert"),
        ("drink", "Drink"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    ingredients = models.TextField(
        default="Ingredients not provided.",
        help_text="List the ingredients for this dish"
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_vegetarian = models.BooleanField(default=False)

    is_popular = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_chef_choice = models.BooleanField(default=False)

    image = models.ImageField(upload_to="menu_images/", blank=True, null=True)

    def save(self, *args, **kwargs):
        # Auto-assign a default placeholder image if none uploaded.
        if not self.image:
            placeholder_path = (
                Path(__file__).resolve().parent / "static" / "images" / "no_image_available.png"
            )
            if placeholder_path.exists():
                with open(placeholder_path, "rb") as f:
                    self.image.save("no_image_available.png", File(f), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Table(models.Model):
    table_number = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} seats)"


class Booking(models.Model):
    name = models.CharField(max_length=100)

    # ✅ Email OR phone: email now optional
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)

    guests = models.PositiveIntegerField()
    date = models.DateField()
    time = models.TimeField()
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=8, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)

    def _generate_reference(self):
        """Return a unique 8-character reference code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Booking.objects.filter(reference=code).exists():
                return code

    def __str__(self):
        return f"{self.name} — {self.date} {self.time} ({self.guests} guests)"
