"""
Management command to render previews of all transactional emails to reports/emails/*.html.
Useful for visual QA and design language fidelity inspection.
"""

from decimal import Decimal
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone


class Command(BaseCommand):
    help = "Renders mock previews of all transactional emails into reports/emails/*.html."

    def handle(self, *args, **options):
        reports_dir = settings.BASE_DIR / "reports" / "emails"
        reports_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write("Rendering email previews...")

        # Mock Order-like object
        class MockItem:
            product_title = "Sony WH-1000XM5 Wireless Noise Cancelling Headphones"
            product_sku = "SONY-WH1000XM5-BLK"
            quantity = 1
            line_total = Decimal("29990.00")

        class MockOrder:
            order_number = "EC-20261007-8899"
            created_at = timezone.now()
            get_payment_method_display = "Razorpay Online"
            items = type("Items", (), {"all": lambda self: [MockItem()]})()
            subtotal = Decimal("29990.00")
            discount_amount = Decimal("1500.00")
            shipping_fee = Decimal("0.00")
            tax_amount = Decimal("4340.85")
            total_amount = Decimal("28490.00")
            is_bill_of_supply = False
            tracking_carrier = "Blue Dart Express"
            tracking_number = "BD-88992211IN"
            shipping_address_snapshot = {
                "full_name": "Aarav Sharma",
                "line1": "Flat 402, Shanti Heights",
                "line2": "14th Main, Indiranagar",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
                "phone": "+91 98765 43210",
            }

        class MockCreditNote:
            credit_note_number = "EC-CN-2026-27-00042"

        order = MockOrder()
        credit_note = MockCreditNote()
        site_url = settings.SITE_URL.rstrip("/")
        order_url = f"{site_url}/orders/{order.order_number}/?token=demo-guest-token-123"

        templates_to_render = [
            (
                "order_confirmation.html",
                "emails/order_confirmation.html",
                {"order": order, "order_url": order_url, "site_url": site_url},
            ),
            (
                "payment_confirmation.html",
                "emails/payment_confirmation.html",
                {"order": order, "payment_id": "pay_O7d89Kf23LmnPQ", "order_url": order_url, "site_url": site_url},
            ),
            (
                "status_update.html",
                "emails/status_update.html",
                {
                    "order": order,
                    "status_display": "Out for Delivery",
                    "carrier": "Blue Dart Express",
                    "tracking_number": "BD-88992211IN",
                    "estimated_delivery": "Today by 7:00 PM",
                    "order_url": order_url,
                    "site_url": site_url,
                },
            ),
            (
                "cancellation_refund.html",
                "emails/cancellation_refund.html",
                {
                    "order": order,
                    "credit_note": credit_note,
                    "refund_amount": order.total_amount,
                    "reason": "Cancelled by customer before dispatch",
                    "order_url": order_url,
                    "site_url": site_url,
                },
            ),
            (
                "cod_placed.html",
                "emails/cod_placed.html",
                {"order": order, "order_url": order_url, "site_url": site_url},
            ),
            (
                "account_email_confirmation_signup.html",
                "account/email/email_confirmation_signup_message.html",
                {"activate_url": f"{site_url}/accounts/confirm-email/key123/", "site_url": site_url},
            ),
            (
                "account_password_reset.html",
                "account/email/password_reset_key_message.html",
                {"password_reset_url": f"{site_url}/accounts/password/reset/key/key123/", "site_url": site_url},
            ),
        ]

        for filename, template_name, ctx in templates_to_render:
            out_path = reports_dir / filename
            rendered = render_to_string(template_name, ctx)
            out_path.write_text(rendered, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"  Saved preview: {out_path}"))

        self.stdout.write(self.style.SUCCESS("All email previews successfully rendered."))
