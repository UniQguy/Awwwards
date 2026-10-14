#!/usr/bin/env python3
"""
Cache or generate local image assets for catalog demonstration products (WP7).
Stores assets locally in media/products/ so the storefront functions 100% offline
with zero reliance on external CDNs or external image hosts.
"""

from io import BytesIO
import os
from pathlib import Path
import sys
import urllib.request

import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw
from apps.catalog.models import Product, ProductMedia

MEDIA_DIR = BASE_DIR / "media" / "products"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

PALETTES = {
    "earphones-headphones": (245, 242, 235),
    "speakers": (242, 239, 233),
    "smartphones": (235, 240, 237),
    "smartwatches-bands": (237, 236, 232),
    "cameras": (240, 237, 230),
    "tvs": (235, 240, 245),
    "keyboards-mice": (237, 242, 234),
    "cables-chargers-powerbanks": (243, 239, 234),
    "cases-protectors": (239, 236, 238),
    "other": (239, 240, 241),
}


def generate_local_svg_plate(product: Product) -> ContentFile:
    """Generates a calibrated local WebP product plate with Pillow."""
    cat_slug = product.category.slug if product.category else "other"
    bg = PALETTES.get(cat_slug, (240, 240, 240))
    img = Image.new("RGB", (600, 600), color=bg)
    draw = ImageDraw.Draw(img)

    # Draw refined geometric hardware representation
    draw.rectangle([60, 60, 540, 540], outline=(200, 195, 185), width=2)
    draw.ellipse([200, 200, 400, 400], outline=(150, 145, 135), width=3)

    buf = BytesIO()
    img.save(buf, format="WEBP", quality=85)
    return ContentFile(buf.getvalue(), name=f"{product.slug[:30]}.webp")


def cache_demo_images(limit: int = 50):
    """
    Caches local images for featured, collection, and top products.
    Attempts network download with short timeout; if offline, generates calibrated local WebP.
    """
    featured_qs = (
        Product.objects.filter(is_available=True)
        .order_by("-source_rating_count")[:limit]
    )
    print(f"Checking local image caching for top {featured_qs.count()} products...")

    cached_count = 0
    generated_count = 0

    for prod in featured_qs:
        media = prod.media.first()
        if not media:
            media = ProductMedia.objects.create(
                product=prod,
                alt_text=prod.display_name,
                display_order=0,
            )

        if media.local_image and os.path.exists(media.local_image.path):
            continue

        file_saved = False
        if media.external_image_url and media.external_image_url.startswith("http"):
            try:
                req = urllib.request.Request(
                    media.external_image_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        ext = os.path.splitext(media.external_image_url.split("?")[0])[1] or ".jpg"
                        media.local_image.save(f"{prod.slug[:30]}{ext}", ContentFile(content), save=True)
                        cached_count += 1
                        file_saved = True
            except Exception:
                file_saved = False

        if not file_saved:
            # Generate offline fallback WebP plate
            content_file = generate_local_svg_plate(prod)
            media.local_image.save(content_file.name, content_file, save=True)
            generated_count += 1

    print(f"Image caching complete: {cached_count} downloaded, {generated_count} locally generated.")


if __name__ == "__main__":
    cache_demo_images()
