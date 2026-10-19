"""
Management command to seed curated editorial collections and featured product slots.
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Collection, FeaturedProduct, Product


class Command(BaseCommand):
    help = "Seeds editorial monograph collections with featured product plinths."

    def handle(self, *args, **options):
        self.stdout.write("Seeding curated editorial collections...")

        collections_data = [
            {
                "title": "The Kinetic Monograph",
                "slug": "kinetic-monograph",
                "intro": "Flagship computing and sensory electronics curated for quiet performance and editorial focus.",
                "cat_slugs": ["smartphones", "smartwatches-bands"],
            },
            {
                "title": "Studio Acoustics",
                "slug": "studio-acoustics",
                "intro": "Reference headphones, acoustic monitors, and pure high-fidelity transducers.",
                "cat_slugs": ["earphones-headphones", "speakers"],
            },
            {
                "title": "Tactile Workstation",
                "slug": "tactile-workstation",
                "intro": "Precision mechanical keyboards, calibrated pointers, and minimalist desk architecture.",
                "cat_slugs": ["keyboards-mice"],
            },
            {
                "title": "GaN Power Architecture",
                "slug": "gan-power-architecture",
                "intro": "Gallium Nitride charging hubs, braided conductors, and high-density magnetic batteries.",
                "cat_slugs": ["cables-chargers-powerbanks"],
            },
        ]

        with transaction.atomic():
            for idx, c_data in enumerate(collections_data):
                col, created = Collection.objects.update_or_create(
                    slug=c_data["slug"],
                    defaults={
                        "title": c_data["title"],
                        "intro": c_data["intro"],
                        "is_active": True,
                        "display_order": idx + 1,
                        "is_sample_data": True,
                    },
                )

                # Assign 4 products per collection prioritizing flagship hardware
                matching_prods = list(
                    Product.objects.filter(
                        category__slug__in=c_data["cat_slugs"],
                        is_available=True,
                        selling_price__gte=Decimal("15000.00") if idx == 0 else Decimal("3000.00"),
                        media__media_type="image",
                    ).order_by("-selling_price", "-source_rating_count")[:4]
                )
                if len(matching_prods) < 4:
                    matching_prods = list(
                        Product.objects.filter(
                            category__slug__in=c_data["cat_slugs"],
                            is_available=True,
                            selling_price__gt=Decimal("0.00"),
                            media__media_type="image",
                        ).order_by("-selling_price", "-source_rating_count")[:4]
                    )

                col.featured_items.all().delete()
                for p_idx, prod in enumerate(matching_prods):
                    FeaturedProduct.objects.create(
                        collection=col,
                        product=prod,
                        display_order=p_idx + 1,
                        is_hero=(p_idx == 0),
                        callout="Editor's Selection" if p_idx == 0 else "",
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {len(collections_data)} curated collections.")
        )
