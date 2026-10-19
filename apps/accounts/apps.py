from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Customer Accounts & Profiles"

    def ready(self):
        import apps.accounts.signals  # noqa
        try:
            from django.apps import apps
            allauth_config = apps.get_app_config("account")
            allauth_config.verbose_name = "Email addresses and sign-in (Allauth)"
        except LookupError:
            pass
