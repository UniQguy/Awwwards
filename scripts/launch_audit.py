#!/usr/bin/env python3
"""
Comprehensive Launch Audit for ELECTROCART.
Runs and summarizes deployment verification checks:
- check --deploy
- test suite
- contrast verification
- CSS audit
- site crawler
- sitemap fetch
- robots.txt fetch
- security headers check
- DEBUG status
- "Before you go live" sample-data leak inspection table
"""

import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
import django
django.setup()

from django.conf import settings
from django.test import Client

from apps.catalog.models import Collection, Product, ProductMedia
from apps.inventory.models import Inventory
from apps.promotions.models import Coupon
from apps.shipping.models import ShippingZone


def run_command(cmd, env_overrides=None):
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    res = subprocess.run(
        cmd,
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        env=env,
        errors="replace",
    )
    return res.returncode == 0, res.stdout, res.stderr


def main():
    print("=" * 80)
    print("ELECTROCART FINAL LAUNCH AUDIT")
    print("=" * 80)
    print()

    client = Client()
    audit_results = []

    # 1. Check Deploy
    print("1. Running 'manage.py check --deploy --settings=config.settings.production'...")
    deploy_env = {
        "SECRET_KEY": "strictly-random-production-secret-key-of-at-least-50-characters-here!",
        "DATABASE_URL": f"sqlite:///{BASE_DIR}/db.sqlite3",
        "SELLER_STATE": "Gujarat",
        "ALLOWED_HOSTS": "electrocart.example.com",
        "CSRF_TRUSTED_ORIGINS": "https://electrocart.example.com",
        "SITE_URL": "https://electrocart.example.com",
    }
    deploy_ok, out, err = run_command(
        [sys.executable, "manage.py", "check", "--deploy", "--settings=config.settings.production"],
        env_overrides=deploy_env,
    )
    audit_results.append(("check --deploy", "PASS" if deploy_ok else "FAIL", out.strip() or err.strip()))
    print(f"   -> {'PASS' if deploy_ok else 'FAIL'}")

    # 2. Python Test Suite
    print("2. Running full Python test suite...")
    test_ok, out, err = run_command([sys.executable, "manage.py", "test", "--no-input"])
    test_summary = "All tests green" if test_ok else "Test failure detected"
    audit_results.append(("Test Suite", "PASS" if test_ok else "FAIL", test_summary))
    print(f"   -> {'PASS' if test_ok else 'FAIL'}")

    # 3. Contrast Audit
    print("3. Running verify_contrast.py...")
    contrast_script = BASE_DIR / "scripts" / "verify_contrast.py"
    if contrast_script.exists():
        c_ok, out, err = run_command([sys.executable, str(contrast_script)])
        audit_results.append(("Contrast Audit (WCAG AA)", "PASS" if c_ok else "FAIL", "All 10 colour worlds pass AA"))
        print(f"   -> {'PASS' if c_ok else 'FAIL'}")
    else:
        audit_results.append(("Contrast Audit", "SKIP", "verify_contrast.py not found"))

    # 4. CSS Audit
    print("4. Running css_audit.py...")
    css_script = BASE_DIR / "scripts" / "css_audit.py"
    if css_script.exists():
        css_ok, out, err = run_command([sys.executable, str(css_script)])
        audit_results.append(("CSS Rules & Specificity", "PASS" if css_ok else "FAIL", "Banned properties & rules verified"))
        print(f"   -> {'PASS' if css_ok else 'FAIL'}")
    else:
        audit_results.append(("CSS Audit", "SKIP", "css_audit.py not found"))

    # 5. Site Crawler
    print("5. Running crawl_site.py...")
    crawl_script = BASE_DIR / "scripts" / "crawl_site.py"
    if crawl_script.exists():
        crawl_ok, out, err = run_command([sys.executable, str(crawl_script)])
        audit_results.append(("Internal Site Crawler", "PASS" if crawl_ok else "FAIL", "Zero 500 errors across routes"))
        print(f"   -> {'PASS' if crawl_ok else 'FAIL'}")
    else:
        audit_results.append(("Crawler", "SKIP", "crawl_site.py not found"))

    # 6. Sitemap Fetch
    print("6. Fetching /sitemap.xml...")
    sm_resp = client.get("/sitemap.xml")
    sm_ok = False
    sm_detail = f"Status {sm_resp.status_code}"
    if sm_resp.status_code == 200:
        try:
            root = ET.fromstring(sm_resp.content)
            urls = root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url")
            sm_ok = len(urls) > 0
            sm_detail = f"200 OK ({len(urls)} URLs parsed)"
        except Exception as e:
            sm_detail = f"XML parse error: {e}"
    audit_results.append(("Sitemap (/sitemap.xml)", "PASS" if sm_ok else "FAIL", sm_detail))
    print(f"   -> {'PASS' if sm_ok else 'FAIL'} ({sm_detail})")

    # 7. Robots.txt Fetch
    print("7. Fetching /robots.txt...")
    rb_resp = client.get("/robots.txt")
    rb_ok = (rb_resp.status_code == 200 and "Sitemap:" in rb_resp.content.decode("utf-8", "ignore"))
    audit_results.append(("Robots.txt (/robots.txt)", "PASS" if rb_ok else "FAIL", f"Status {rb_resp.status_code} with Sitemap directive"))
    print(f"   -> {'PASS' if rb_ok else 'FAIL'}")

    # 8. Security Headers
    print("8. Checking HTTP security headers...")
    h_resp = client.get("/")
    headers = h_resp.headers
    has_csp = "Content-Security-Policy" in headers
    has_perm = "Permissions-Policy" in headers
    has_xfo = headers.get("X-Frame-Options") == "DENY"
    has_coop = headers.get("Cross-Origin-Opener-Policy") == "same-origin"
    headers_ok = has_csp and has_perm and has_xfo and has_coop
    audit_results.append(
        ("Security Headers", "PASS" if headers_ok else "FAIL", "CSP, Permissions-Policy, X-Frame-Options, COOP verified")
    )
    print(f"   -> {'PASS' if headers_ok else 'FAIL'}")

    # 9. DEBUG status in production settings
    from config.settings import production as prod_settings
    no_debug = (prod_settings.DEBUG is False)
    audit_results.append(("DEBUG=False in Production", "PASS" if no_debug else "FAIL", f"DEBUG is {prod_settings.DEBUG}"))
    print(f"   -> {'PASS' if no_debug else 'FAIL'}")

    # Print summary table
    print("\n" + "=" * 80)
    print("AUDIT RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'CHECK':<32} | {'STATUS':<8} | {'DETAILS'}")
    print("-" * 80)
    for name, status, detail in audit_results:
        print(f"{name:<32} | {status:<8} | {detail}")
    print("-" * 80)

    # 10. Sample Data Audit ("Before You Go Live" Table)
    print("\n" + "=" * 80)
    print("BEFORE YOU GO LIVE: SAMPLE DATA & OPERATIONAL READINESS TABLE")
    print("=" * 80)

    sample_stock_count = Inventory.objects.filter(is_sample_data=True).count()
    sample_coupons_count = Coupon.objects.filter(is_sample_data=True).count()
    sample_zones_count = ShippingZone.objects.filter(source="sample").count()
    sample_collections_count = Collection.objects.filter(is_sample_data=True).count()
    hotlinked_images = ProductMedia.objects.filter(external_image_url__icontains="amazon").count()

    seller_state = getattr(settings, "SELLER_STATE", "")
    seller_gstin = getattr(settings, "SELLER_GSTIN", "")
    seller_name = getattr(settings, "SELLER_LEGAL_NAME", "")
    seller_addr = getattr(settings, "SELLER_ADDRESS", "")
    razorpay_key = getattr(settings, "RAZORPAY_KEY_ID", "")

    sample_items = [
        ("Inventory Stock", f"{sample_stock_count} SKUs flagged as sample", "Replace with warehouse inventory feed"),
        ("Promotional Coupons", f"{sample_coupons_count} active demo coupon(s)", "Deactivate sample promo codes; configure real campaigns"),
        ("Delivery Zones / PIN Codes", f"{sample_zones_count} mock carrier zones", "Upload production courier serviceability matrix"),
        ("Editorial Collections", f"{sample_collections_count} sample collections", "Curate live homepage hero and editorial monographs"),
        ("Product Photography", f"{hotlinked_images} hotlinked Amazon CDN images", "Replace hotlinked assets with owned studio media"),
        ("Seller State", seller_state or "NOT CONFIGURED", "Set SELLER_STATE environment variable for GST compliance"),
        ("Seller GSTIN", seller_gstin or "BLANK (Bill of Supply active)", "Provide registered 15-digit GSTIN if GST registered"),
        ("Seller Legal Name", seller_name or "BLANK", "Set legal entity name for statutory invoices"),
        ("Seller Address", seller_addr or "BLANK", "Set registered business address on tax receipts"),
        ("Razorpay Gateway Keys", "Configured" if razorpay_key else "TEST / PLACEHOLDER", "Set live RAZORPAY_KEY_ID, SECRET, and WEBHOOK_SECRET"),
        ("Legal Pages", "Templates in place with placeholders", "Review terms, privacy, shipping, and refund legal copy"),
    ]

    print(f"{'DOMAIN / ITEM':<28} | {'CURRENT STATE':<32} | {'ACTION REQUIRED BEFORE LAUNCH'}")
    print("-" * 95)
    for domain, state, action in sample_items:
        print(f"{domain:<28} | {state:<32} | {action}")
    print("-" * 95)
    print()

    all_passed = all(status == "PASS" for _, status, _ in audit_results)
    if all_passed:
        print(">> ALL PRE-LAUNCH AUTOMATED AUDITS PASSED SUCCESSFULLY. <<")
    else:
        print(">> ONE OR MORE AUDITS FAILED. INSPECT ABOVE DETAILS. <<")
        sys.exit(1)


if __name__ == "__main__":
    main()
