from django.apps import apps
from importlib import import_module


def autodiscover_registries():
    for app_config in apps.get_app_configs():
        try:
            import_module(f"{app_config.name}.registry")
        except ModuleNotFoundError:
            continue