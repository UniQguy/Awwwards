"""
URL patterns for customer account management.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.account_dashboard, name="account_dashboard"),
    path("orders/", views.account_order_list, name="account_order_list"),
    path("orders/<str:order_number>/", views.account_order_detail, name="account_order_detail"),
    path("addresses/", views.account_address_list, name="account_address_list"),
    path("addresses/create/", views.account_address_form, name="account_address_create"),
    path("addresses/<uuid:uuid>/edit/", views.account_address_form, name="account_address_edit"),
    path("addresses/<uuid:uuid>/delete/", views.account_address_delete, name="account_address_delete"),
    path("addresses/<uuid:uuid>/default/", views.account_address_set_default, name="account_address_set_default"),
    path("profile/", views.account_profile, name="account_profile"),
]
