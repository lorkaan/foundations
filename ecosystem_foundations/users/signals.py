# users/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .services.role_sync import sync_roles

@receiver(post_migrate)
def sync_roles_handler(sender, **kwargs):
    sync_roles()