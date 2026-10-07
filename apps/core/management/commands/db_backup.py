"""
Management command to perform a non-blocking online backup of the SQLite database.
Utilizes the official sqlite3 online backup API and enforces a configurable retention policy.
"""

from datetime import datetime
import os
from pathlib import Path
import sqlite3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Creates a point-in-time online backup of SQLite database using sqlite3 backup API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=str,
            default=os.environ.get("BACKUP_DIR", str(settings.BASE_DIR / "backups")),
            help="Directory path where database backup files will be stored.",
        )
        parser.add_argument(
            "--retention",
            type=int,
            default=int(os.environ.get("BACKUP_RETENTION", 7)),
            help="Number of most recent backup archives to retain (older ones are pruned).",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"]).resolve()
        retention = options["retention"]

        if connection.vendor != "sqlite":
            self.stdout.write(
                self.style.WARNING(
                    f"Current database vendor is '{connection.vendor}'. "
                    "Online file backup is designed for SQLite; use pg_dump for PostgreSQL."
                )
            )
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"electrocart_backup_{timestamp}.sqlite3"
        backup_path = output_dir / backup_filename

        self.stdout.write(f"Initiating online backup of SQLite database to: {backup_path}")

        # Ensure active database connection
        connection.ensure_connection()
        source_connection = connection.connection

        # Execute online backup
        try:
            dest_conn = sqlite3.connect(str(backup_path))
            with dest_conn:
                source_connection.backup(dest_conn, pages=100, sleep=0.01)
            dest_conn.close()
        except Exception as exc:
            raise CommandError(f"Database backup failed: {exc}") from exc

        file_size_bytes = backup_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        self.stdout.write(
            self.style.SUCCESS(
                f"Backup completed successfully: {backup_filename} ({file_size_mb:.2f} MB)"
            )
        )

        # Enforce retention policy
        existing_backups = sorted(
            [f for f in output_dir.glob("electrocart_backup_*.sqlite3") if f.is_file()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if len(existing_backups) > retention:
            to_delete = existing_backups[retention:]
            for old_file in to_delete:
                try:
                    old_file.unlink()
                    self.stdout.write(f"Pruned expired backup archive: {old_file.name}")
                except OSError as err:
                    self.stdout.write(self.style.WARNING(f"Could not remove {old_file.name}: {err}"))

        remaining = min(len(existing_backups), retention)
        self.stdout.write(f"Retained {remaining} backup archive(s) in {output_dir}")
