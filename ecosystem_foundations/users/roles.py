from .registry import register_role

register_role("admin", "Admin", system=True)
register_role("staff", "Staff", system=True)
register_role("guest", "Guest", system=True)