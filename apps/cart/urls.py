"""
URL routes for shopping cart and coupon management.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("add-bundle/", views.cart_add_bundle, name="cart_add_bundle"),
    path("update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("save-for-later/<int:product_id>/", views.cart_save_for_later, name="cart_save_for_later"),
    path("move-to-bag/<int:product_id>/", views.cart_move_to_bag, name="cart_move_to_bag"),
    path("clear/", views.cart_clear, name="cart_clear"),
    path("coupon/apply/", views.coupon_apply, name="coupon_apply"),
    path("coupon/remove/", views.coupon_remove, name="coupon_remove"),
]
