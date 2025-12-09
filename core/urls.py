"""
URL configuration for the core app.

This file maps URL paths to view functions within the core app.
It's included in the main wordle_stats/urls.py using include().
"""
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard - the main page users see after login
    path('', views.dashboard, name='dashboard'),
]
