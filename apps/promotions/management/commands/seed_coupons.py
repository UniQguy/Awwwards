"""
Management command to seed realistic sample coupons for demonstration and testing.
"""

from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import Category
from apps.promotions.models import Coupon


class Command(BaseCommand):
    help = "Seeds sample promotional coupon codes (WELCOME10, FLAT500, AUDIO20, FREESHIP)."

    def handle(self, *args, **options):
        now = timezone.now()
        start = now - timedelta(days=30)
        end = now + timedelta(days=365 * 3)

        # 1. WELCOME10
        welcome10, _ = Coupon.objects.update_or_create(
            code="WELCOME10",
            defaults={
                "description": "10% off your entire order up to ₹500 (Min order ₹999)",
                "discount_type": Coupon.TYPE_PERCENTAGE,
                "discount_value": Decimal("10.00"),
                "min_order_amount": Decimal("999.00"),
                "max_discount_amount": Decimal("500.00"),
                "usage_limit_per_user": 1,
                "valid_from": start,
                "valid_until": end,
                "is_active": True,
                "is_sample_data": True,
            },
        )

        # 2. FLAT500
        flat500, _ = Coupon.objects.update_or_create(
            code="FLAT500",
            defaults={
                "description": "Flat ₹500 discount on orders above ₹4,999",
                "discount_type": Coupon.TYPE_FIXED,
                "discount_value": Decimal("500.00"),
                "min_order_amount": Decimal("4999.00"),
                "max_discount_amount": None,
                "usage_limit_per_user": 2,
                "valid_from": start,
                "valid_until": end,
                "is_active": True,
                "is_sample_data": True,
            },
        )

        # 3. AUDIO20 (Restricted to audio categories)
        audio20, _ = Coupon.objects.update_or_create(
            code="AUDIO20",
            defaults={
                "description": "20% off high-fidelity audio equipment up to ₹1,000 (Min order ₹1,499)",
                "discount_type": Coupon.TYPE_PERCENTAGE,
                "discount_value": Decimal("20.00"),
                "min_order_amount": Decimal("1499.00"),
                "max_discount_amount": Decimal("1000.00"),
                "usage_limit_per_user": 3,
                "valid_from": start,
                "valid_until": end,
                "is_active": True,
                "is_sample_data": True,
            },
        )
        audio_cats = Category.objects.filter(slug__in=["earphones-headphones", "speakers"])
        audio20.applicable_categories.set(audio_cats)

        # 4. FREESHIP
        freeship, _ = Coupon.objects.update_or_create(
            code="FREESHIP",
            defaults={
                "description": "Complimentary delivery on orders above ₹199",
                "discount_type": Coupon.TYPE_FIXED,
                "discount_value": Decimal("40.00"),
                "min_order_amount": Decimal("199.00"),
                "max_discount_amount": None,
                "usage_limit_per_user": 5,
                "valid_from": start,
                "valid_until": end,
                "is_active": True,
                "is_sample_data": True,
            },
        )

        self.stdout.write(
            self.style.SUCCESS("Sample coupons seeded: WELCOME10, FLAT500, AUDIO20, FREESHIP.")
        )
