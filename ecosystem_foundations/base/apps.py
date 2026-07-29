from django.apps import AppConfig


class BaseConfig(AppConfig):
    name = 'foundations.ecosystem_foundations.base'

    def ready(self):
        from ..plugins.registry_discovery import autodiscover_registries

        autodiscover_registries()