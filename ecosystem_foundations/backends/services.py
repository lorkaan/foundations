from .registry import backend_registry


def get_backend(name, **config):
    return backend_registry.create(
        name,
        **config
    )