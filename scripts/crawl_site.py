#!/usr/bin/env python3
"""
Internal Site Crawler for ELECTROCART.
Crawls all internal HTML links starting from the homepage using the Django test Client.
Verifies that no storefront page throws a 500 server error or broken internal link.
"""

from collections import deque
from html.parser import HTMLParser
import os
import sys
from pathlib import Path
import urllib.parse

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
import django
django.setup()

from django.test import Client


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, val in attrs:
                if attr == "href" and val:
                    self.links.append(val)


def normalize_url(url: str, current_path: str) -> str | None:
    """Normalize internal URL and ignore anchors, mailto, and external domains."""
    url = url.strip()
    if not url or url.startswith("#") or url.startswith("mailto:") or url.startswith("tel:"):
        return None

    parsed = urllib.parse.urlparse(url)
    if parsed.netloc:
        return None  # External domain

    path = parsed.path
    if not path.startswith("/"):
        path = urllib.parse.urljoin(current_path, path)

    # Ignore admin, static, media, logout POST actions, etc.
    if path.startswith("/admin/") or path.startswith("/static/") or path.startswith("/media/"):
        return None

    # Exclude mutation POST routes from crawling GET requests
    mutation_prefixes = [
        "/cart/add/", "/cart/update/", "/cart/remove/", "/cart/clear/",
        "/cart/coupon/", "/wishlist/toggle/", "/wishlist/move-to-cart/",
        "/wishlist/remove/", "/compare/add/", "/compare/remove/", "/compare/clear/",
        "/orders/cancel/", "/accounts/logout/", "/account/addresses/",
    ]
    if any(path.startswith(prefix) for prefix in mutation_prefixes) and not path.endswith("/"):
        return None

    # Keep query if present
    query = parsed.query
    return f"{path}?{query}" if query else path


def crawl_storefront(max_pages: int = 100) -> bool:
    client = Client()
    visited = set()
    queue = deque(["/"])
    success_count = 0
    errors = []

    print("\n" + "=" * 80)
    print("ELECTROCART STOREFRONT LINK CRAWLER (Phase 3 Quality Gate)")
    print("=" * 80)

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        try:
            response = client.get(url, follow=True)
            status = response.status_code

            if status >= 500:
                errors.append((url, status, "Server Error (500)"))
                print(f"[FAIL {status}] {url}")
            elif status >= 400:
                errors.append((url, status, "Client Error (400+)"))
                print(f"[FAIL {status}] {url}")
            else:
                success_count += 1
                if success_count <= 25 or success_count % 10 == 0:
                    print(f"[OK {status}] {url}")

            # Extract internal links from HTML responses
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type:
                parser = LinkExtractor()
                parser.feed(response.content.decode("utf-8", errors="ignore"))
                for raw_link in parser.links:
                    norm = normalize_url(raw_link, url)
                    if norm and norm not in visited:
                        queue.append(norm)

        except Exception as exc:
            errors.append((url, 500, str(exc)))
            print(f"[ERROR] {url} -> {exc}")

    print("-" * 80)
    print(f"Crawled {len(visited)} URLs: {success_count} passed, {len(errors)} failed.")
    print("=" * 80 + "\n")

    if errors:
        print("Crawler detected broken links:")
        for u, s, msg in errors:
            print(f"  - {u} (Status {s}): {msg}")
        return False

    print("ALL CRAWLED STOREFRONT URLS RETURNED HEALTHY STATUS (Zero Broken Links).")
    return True


if __name__ == "__main__":
    passed = crawl_storefront(max_pages=80)
    sys.exit(0 if passed else 1)
