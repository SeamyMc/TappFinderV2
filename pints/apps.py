from django.apps import AppConfig


class PintsConfig(AppConfig):
    name = 'pints'

    def ready(self):
        from . import signals  # noqa: F401
