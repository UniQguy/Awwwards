"""
Sitemaps configuration for search engine indexing.
Includes:
- Static pages (Home, About, Categories, Brands, Legal Policies)
- Active Categories (/c/<slug>/)
- Purchasable Products (/p/<slug>/)
Configured cleanly without django.contrib.sites database dependency.
"""

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import Category, Product


class BaseMonographSitemap(Sitemap):
    protocol = "https" if getattr(settings, "SECURE_SSL_REDIRECT", False) else "http"


class StaticViewSitemap(BaseMonographSitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "about",
            "category_list",
            "brand_list",
            "legal_terms",
            "legal_privacy",
            "legal_shipping",
            "legal_refunds",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(BaseMonographSitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Category.objects.filter(is_active=True).order_by("name")

    def location(self, obj):
        return reverse("category_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class ProductSitemap(BaseMonographSitemap):
    priority = 0.9
    changefreq = "daily"

    def items(self):
        return Product.objects.filter(is_available=True).order_by("display_name")

    def location(self, obj):
        return reverse("product_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}
