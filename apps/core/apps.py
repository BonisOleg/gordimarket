from django.apps import AppConfig


def _register_sqlite_unicode_lower(sender, connection, **kwargs):
    """Override SQLite's ASCII-only LOWER() with Python's str.lower() for full Unicode support."""
    if connection.vendor == 'sqlite':
        connection.connection.create_function(
            'LOWER', 1, lambda s: s.lower() if s else s
        )


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Основні компоненти'

    def ready(self):
        from django.db.backends.signals import connection_created
        connection_created.connect(_register_sqlite_unicode_lower)
