"""
Management command to seed the 10 canonical editorial categories with confirmed HSN and GST rates.
"""

from django.core.management.base import BaseCommand
from apps.catalog.models import Category
from apps.catalog.services.category_rules import CATEGORY_DEFINITIONS, merge_duplicate_categories


class Command(BaseCommand):
    help = "Seeds the 10 canonical categories with HSN codes, GST rates, and colour worlds, merging duplicates."

    def handle(self, *args, **options):
        # 1. Merge any duplicate or non-canonical categories first
        cleanup_stats = merge_duplicate_categories()
        if cleanup_stats["deleted_categories"] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Merged duplicate categories: {cleanup_stats['deleted_categories']} deleted, "
                    f"{cleanup_stats['reassigned_products']} products reassigned."
                )
            )

        created_count = 0
        updated_count = 0

        for item in CATEGORY_DEFINITIONS:
            category, created = Category.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "accent_key": item["accent_key"],
                    "hsn_code": item["hsn_code"],
                    "gst_rate": item["gst_rate"],
                    "is_gst_rate_verified": item["is_gst_rate_verified"],
                    "display_order": item["display_order"],
                    "description": item["description"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Categories seeded successfully: {created_count} created, {updated_count} updated. Total: {len(CATEGORY_DEFINITIONS)}"
            )
        )
