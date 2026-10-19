"""
URL routes for shipping serviceability and delivery estimates.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("check/", views.shipping_check, name="shipping_check"),
    path("estimate/", views.shipping_check, name="shipping_estimate"),
]
