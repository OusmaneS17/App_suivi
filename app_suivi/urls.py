from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard_app.urls'), name='dashboard'),  # Include the dashboard app URLs
]