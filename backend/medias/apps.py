from importlib import import_module

from django.apps import AppConfig


class MediasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "medias"

    def ready(self):
        import_module("medias.signals")
