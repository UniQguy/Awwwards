"""
Management command to release expired stock reservations.
"""

from django.core.management.base import BaseCommand
from apps.inventory.services.reservation_service import cleanup_expired_reservations


class Command(BaseCommand):
    help = "Releases all expired stock reservations whose TTL has lapsed."

    def handle(self, *args, **options):
        released = cleanup_expired_reservations()
        self.stdout.write(
            self.style.SUCCESS(f"Released {released} expired stock reservations.")
        )
