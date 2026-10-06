"""
URL patterns for payments application.
"""

from django.urls import path
from apps.payments.views import razorpay_verify_view, razorpay_webhook_view

app_name = "payments"

urlpatterns = [
    path("razorpay/verify/", razorpay_verify_view, name="razorpay_verify"),
    path("razorpay/webhook/", razorpay_webhook_view, name="razorpay_webhook"),
]
