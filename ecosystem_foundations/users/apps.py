from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'foundations.ecosystem_foundations.users'

    def ready(self):
        from ..users.registry import USER_ROLE_REGISTRY
        from .services.role_sync import sync_roles

        sync_roles()
        USER_ROLE_REGISTRY.lock()
