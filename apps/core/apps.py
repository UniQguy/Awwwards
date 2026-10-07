from django.apps import AppConfig
from django.db.backends.signals import connection_created


def configure_sqlite_pragmas(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        with connection.cursor() as cursor:
            # WAL mode allows concurrent readers while a write occurs
            cursor.execute("PRAGMA journal_mode=WAL;")
            # NORMAL synchronous is safe in WAL mode and drastically cuts fsync calls
            cursor.execute("PRAGMA synchronous=NORMAL;")
            # 64MB memory page cache (-64000 KiB)
            cursor.execute("PRAGMA cache_size=-64000;")
            # 5-second busy timeout to prevent immediate database lock failures
            cursor.execute("PRAGMA busy_timeout=5000;")


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        connection_created.connect(configure_sqlite_pragmas)
