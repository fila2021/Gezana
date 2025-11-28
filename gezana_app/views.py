from django.shortcuts import render

def home(request):
    return render(request, 'gezana_app/home.html')
