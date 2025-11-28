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
