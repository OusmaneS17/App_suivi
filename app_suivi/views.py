
from django.http import HttpResponse # Import HttpResponse to create HTTP responses
from django.shortcuts import render # Import render to render templates

def home_view(request):
    return render(request, 'home.html')


def dashboard_view(request):
    return render(request, 'dashboard.html') # Render the dashboard.html template

def table_view(request):
    return render(request, 'tables.html')

def profile_view(request):
    return render(request, 'profiles.html')


def notification_view(request):
    return render(request, 'notifications.html') 




def base_view(request):
    return render(request, 'base.html') # Render the base.html template



def menu_view(request):
    return render(request, 'menu.html') # Render the menu.html template













#def home_view(request):
#    http_response = HttpResponse("Hello, world!")
#    return http_response
#
#def dashboard_view(request):
#    http_response = HttpResponse("Dashboard")
#    return http_response
#
