"""
URL configuration for wordle_stats project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Django built-in authentication views (login, logout, password reset, etc.)
    # These look for templates in templates/registration/
    path('accounts/', include('django.contrib.auth.urls')),

    # Core app URLs (dashboard, etc.)
    path('', include('core.urls')),
]
