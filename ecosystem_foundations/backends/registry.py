from utils.registry import SingleRegistry
from .exceptions import InvalidBackend, BackendNotFound


class BackendRegistry(SingleRegistry):

    def __init__(self):
        super().__init__()
        self._base_classes = {}


    def register(self, key, base_class=None, *, replace=False):
        """
        Register a backend with optional type enforcement.
        """

        def decorator(cls):

            if base_class and not issubclass(cls, base_class):
                raise InvalidBackend(
                    f"{cls.__name__} must inherit from {base_class.__name__}"
                )

            self._base_classes[key] = base_class

            return super(BackendRegistry, self).register(
                key,
                cls,
                replace=replace
            )

        return decorator


    def create(self, key, **config):
        backend_cls = self.get(key)

        if backend_cls is None:
            raise BackendNotFound(
                f"Backend '{key}' is not registered"
            )

        return backend_cls(**config)
    
BACKEND_REGISTRY = BackendRegistry()