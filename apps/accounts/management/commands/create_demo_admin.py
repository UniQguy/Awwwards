"""
Management command to create a demo administrator and staff manager account (WP2.1).
Strict security rules:
- Reads DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD from the environment.
- Refuses to execute if either is missing.
- Refuses to execute when settings.DEBUG is False.
- Reads optional DEMO_STAFF_EMAIL and DEMO_STAFF_PASSWORD (defaults to staff@electrocart.test with DEMO_ADMIN_PASSWORD).
- Creates a "Store manager" group with sensible model permissions.
- Writes credentials reminder file docs/DEMO_CREDENTIALS.local.md containing emails and reminders ONLY (never passwords).
"""

import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from allauth.account.models import EmailAddress

User = get_user_model()


class Command(BaseCommand):
    help = "Creates or updates demo administrator and store manager staff accounts from environment variables."

    def handle(self, *args, **options):
        # 1. Debug safety guard
        if not getattr(settings, "DEBUG", False):
            raise CommandError("Refusing to create demo accounts: settings.DEBUG is False.")

        # 2. Environment variable check for Admin
        admin_email = os.environ.get("DEMO_ADMIN_EMAIL")
        admin_password = os.environ.get("DEMO_ADMIN_PASSWORD")

        if not admin_email or not admin_password:
            raise CommandError(
                "Missing required environment variables: DEMO_ADMIN_EMAIL and DEMO_ADMIN_PASSWORD must both be set."
            )

        # 3. Create or update Superuser Administrator
        admin_user, admin_created = User.objects.get_or_create(
            email=admin_email,
            defaults={"is_staff": True, "is_superuser": True},
        )
        admin_user.set_password(admin_password)
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        # Mark email verified
        EmailAddress.objects.update_or_create(
            user=admin_user,
            email=admin_email,
            defaults={"verified": True, "primary": True},
        )

        admin_status = "Created" if admin_created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{admin_status} demo administrator: {admin_email}"))

        # 4. Setup "Store manager" Group with Sensible Permissions
        manager_group, _ = Group.objects.get_or_create(name="Store manager")

        # Define sensible permissions for a Store Manager:
        # Catalog: view/add/change Product, Category, Collection, ProductMedia, ProductSpecification
        # Inventory: view/change Inventory
        # Orders: view/change Order, OrderItem, Invoice
        # Promotions: view/add/change Coupon
        # Accounts: view User, Address
        manager_permissions = []
        app_models = {
            "catalog": ["product", "category", "collection", "productmedia", "productspecification"],
            "inventory": ["inventory"],
            "orders": ["order", "orderitem", "invoice"],
            "promotions": ["coupon"],
            "accounts": ["user", "address"],
        }

        from django.db.models import Q
        for app_label, model_names in app_models.items():
            for m_name in model_names:
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=m_name)
                    perms = Permission.objects.filter(
                        content_type=ct
                    ).filter(
                        Q(codename__startswith="view_")
                        | Q(codename__startswith="change_")
                        | Q(codename__startswith="add_")
                    )
                    manager_permissions.extend(perms)
                except ContentType.DoesNotExist:
                    pass

        manager_group.permissions.set(manager_permissions)
        self.stdout.write(f"Configured 'Store manager' group with {len(manager_permissions)} permissions.")

        # 5. Create or update Store Manager Staff User
        staff_email = os.environ.get("DEMO_STAFF_EMAIL", "staff@electrocart.test")
        staff_password = os.environ.get("DEMO_STAFF_PASSWORD", admin_password)

        staff_user, staff_created = User.objects.get_or_create(
            email=staff_email,
            defaults={"is_staff": True, "is_superuser": False},
        )
        staff_user.set_password(staff_password)
        staff_user.is_staff = True
        staff_user.is_superuser = False
        staff_user.save()
        staff_user.groups.add(manager_group)

        EmailAddress.objects.update_or_create(
            user=staff_user,
            email=staff_email,
            defaults={"verified": True, "primary": True},
        )

        staff_status = "Created" if staff_created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{staff_status} demo store manager staff: {staff_email}"))

        # 6. Write credentials reminder (NEVER passwords) to docs/DEMO_CREDENTIALS.local.md
        creds_file = settings.BASE_DIR / "docs" / "DEMO_CREDENTIALS.local.md"
        creds_file.parent.mkdir(parents=True, exist_ok=True)
        creds_content = f"""# ELECTROCART Local Demo Credentials (Git-Ignored)

> **Notice:** This file contains account identifiers for local exam evaluation only.
> Passwords are read exclusively from environment variables and are never stored in source files.

## 1. Administrator Account (Superuser)
- **Role:** Superuser / Full System Administrator
- **Email:** `{admin_email}`
- **Password Location:** Configured in local environment variable `DEMO_ADMIN_PASSWORD`.
- **Admin Access URL:** `/admin/`

## 2. Store Manager Account (Staff)
- **Role:** Staff Member in "Store manager" Group
- **Email:** `{staff_email}`
- **Password Location:** Configured in `DEMO_STAFF_PASSWORD` (or `DEMO_ADMIN_PASSWORD`).
- **Permissions:** Product catalog management, order fulfillment, stock adjustment, coupons.
- **Admin Access URL:** `/admin/`
"""
        with open(creds_file, "w", encoding="utf-8") as f:
            f.write(creds_content)

        self.stdout.write(self.style.SUCCESS(f"Wrote credentials reference to {creds_file}"))
