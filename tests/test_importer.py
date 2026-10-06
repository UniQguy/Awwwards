"""
Acceptance and integration tests for catalog importing, seed_categories, and dry-run audit.
"""

from io import StringIO
from django.core.management import call_command
from django.test import TestCase

from apps.catalog.models import Category, Product, ProductMedia, ProductSpecification


class ImporterCommandTests(TestCase):
    def test_seed_categories_command(self):
        out = StringIO()
        call_command("seed_categories", stdout=out)
        self.assertEqual(Category.objects.count(), 10)
        self.assertTrue(Category.objects.filter(slug="smartphones").exists())
        self.assertTrue(Category.objects.filter(slug="cables-chargers-powerbanks").exists())

    def test_import_products_dry_run_zero_db_writes(self):
        call_command("seed_categories")
        initial_count = Product.objects.count()
        out = StringIO()
        call_command("import_products", "--dry-run", stdout=out)
        self.assertEqual(Product.objects.count(), initial_count)
        output_str = out.getvalue()
        self.assertIn("DRY RUN COMPLETE", output_str)
        self.assertIn("0 DB writes", output_str)
