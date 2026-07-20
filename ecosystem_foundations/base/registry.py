from utils.type_utils import isList


class BaseRegistry:
    def __init__(self):
        self._registry = {}

    def get(self, key, default=None):
        return self._registry.get(key, default)

    def __contains__(self, key):
        return key in self._registry
    
    def __getitem__(self, key):
        return self._registry[key]

    def __iter__(self):
        return iter(self._registry)

    def keys(self):
        return self._registry.keys()

    def values(self):
        return self._registry.values()

    def items(self):
        return self._registry.items()

class SingleRegistry(BaseRegistry):
    def register(self, key, value=None, *, replace=False):
        def decorator(obj):
            if not replace and key in self._registry:
                raise ValueError(f"'{key}' is already registered")

            self._registry[key] = obj
            return obj

        if value is None:
            return decorator

        return decorator(value)

class MultiRegistry(BaseRegistry):
    def register(self, key, obj=None):
        def decorator(fn):
            self._registry.setdefault(key, []).append(fn)
            return fn

        if obj is None:
            return decorator

        return decorator(obj)

    def get(self, key):
        return self._registry.get(key, [])
    
class SetRegistry:
    def __init__(self):
        self._registry = set()

    def add(self, values):
        if isList(values):
            try:
                self._registry.update(values)
            except TypeError:
                self._registry.add(values)
        else:
            self._registry.add(values)

    def __contains__(self, value):
        return value in self._registry

    def __iter__(self):
        return iter(self._registry)