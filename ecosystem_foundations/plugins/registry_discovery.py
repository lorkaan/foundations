from django.apps import apps
from importlib import import_module


def autodiscover_registries():
    for app_config in apps.get_app_configs():
        module_path = f"{app_config.name}.registry"

        try:
            import_module(module_path)

        except ModuleNotFoundError as e:
            # Only ignore if the registry module itself is missing
            if e.name != module_path:
                raise