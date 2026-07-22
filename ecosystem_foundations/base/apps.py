from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = 'base'

    def ready(self):
        from plugins.registry_discovery import autodiscover_registries

        autodiscover_registries()