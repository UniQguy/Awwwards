"""
URL patterns for payments application.
"""

from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("razorpay/checkout/<str:order_number>/", views.razorpay_checkout_page, name="razorpay_checkout"),
    path("razorpay/switch-cod/<str:order_number>/", views.razorpay_switch_cod, name="razorpay_switch_cod"),
    path("razorpay/verify/", views.razorpay_verify_view, name="razorpay_verify"),
    path("razorpay/webhook/", views.razorpay_webhook_view, name="razorpay_webhook"),
    path("failed/<str:order_number>/", views.payment_failed, name="payment_failed"),
    path("cancelled/<str:order_number>/", views.payment_cancelled, name="payment_cancelled"),
    path("pending/<str:order_number>/", views.payment_pending, name="payment_pending"),
]
