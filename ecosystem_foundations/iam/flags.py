class PermissionFlag:
    VIEW = 1 << 0
    EDIT = 1 << 1
    ADD = 1 << 2
    DELETE = 1 << 3

    @classmethod
    def has(cls, permissions, flag):
        return bool(permissions & flag)

    @classmethod
    def add(cls, permissions, flag):
        return permissions | flag

    @classmethod
    def remove(cls, permissions, flag):
        return permissions & ~flag