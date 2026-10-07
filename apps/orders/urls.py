"""
URL routes for checkout process, order lifecycle, invoices, and shipment tracking.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Checkout routes
    path("checkout/", views.checkout_start, name="checkout_start"),
    path("checkout/guest/", views.checkout_guest, name="checkout_guest"),
    path("checkout/address/", views.checkout_address, name="checkout_address"),
    path("checkout/review/", views.checkout_review, name="checkout_review"),
    path("checkout/place/", views.checkout_place, name="checkout_place"),

    # Order management
    path("orders/track/", views.order_track_lookup, name="order_track_lookup"),
    path("orders/track/<str:order_number>/verify/", views.order_track_timeline, name="order_track_timeline"),
    path("orders/<str:order_number>/success/", views.order_success, name="order_success"),
    path("orders/<str:order_number>/cancel/", views.order_cancel, name="order_cancel"),
    path("orders/<str:order_number>/invoice/", views.order_invoice, name="order_invoice"),
    path("orders/<str:order_number>/invoice/pdf/", views.order_invoice_pdf, name="order_invoice_pdf"),
    path("orders/<str:order_number>/credit-note/pdf/", views.order_credit_note_pdf, name="order_credit_note_pdf"),
]
