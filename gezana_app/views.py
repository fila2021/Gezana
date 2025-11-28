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

