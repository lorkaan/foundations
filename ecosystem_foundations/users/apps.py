from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'foundations.ecosystem_foundations.users'

    def ready(self):
        # 👇 THIS is what activates your signal
        import foundations.ecosystem_foundations.users.signals  # noqa

        from .registry import USER_ROLE_REGISTRY

        # Only lock registry — NO DB CALLS HERE
        USER_ROLE_REGISTRY.lock()
