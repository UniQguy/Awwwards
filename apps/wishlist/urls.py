"""
URL routes for customer wishlist management.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.wishlist_detail, name="wishlist_detail"),
    path("toggle/<int:product_id>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("move-to-cart/<int:product_id>/", views.wishlist_move_to_cart, name="wishlist_move_to_cart"),
    path("remove/<int:product_id>/", views.wishlist_remove, name="wishlist_remove"),
]
