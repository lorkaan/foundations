from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        from .registry import user_role_registry
        from .services.role_sync import sync_roles

        sync_roles()
        user_role_registry.lock()
