from utils.type_utils import isList
from django.contrib.contenttypes.models import ContentType
from dataclasses import dataclass
from typing import Type
from django.db import models

from typing import TypeVar, Generic, Callable, Dict, Iterable

T = TypeVar("T")


class GenericRegistry(Generic[T]):
    def __init__(
        self,
        key_fn: Callable[[T], object],
        validator: Callable[[T], None] | None = None,
    ):
        self._items: Dict[object, T] = {}
        self._key_fn = key_fn
        self._validator = validator

    def register(self, item: T):
        if self._validator:
            self._validator(item)

        key = self._key_fn(item)

        if key in self._items:
            raise ValueError(f"Duplicate registration for key: {key}")

        self._items[key] = item

    def get_all(self) -> Iterable[T]:
        return self._items.values()

    def get(self, key: object) -> T:
        return self._items[key]

    def __contains__(self, key: object) -> bool:
        return key in self._items

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

class ModelRegistry:
    def __init__(self):
        self._registry = set()

    def add(self, *models_):
        for model in models_:
            if not isinstance(model, type) or not issubclass(model, models.Model):
                raise TypeError(f"{model} is not a Django model")

            ct = ContentType.objects.get_for_model(model)
            self._registry.add(ct)

    def __contains__(self, value):
        if isinstance(value, ContentType):
            return value in self._registry

        if isinstance(value, models.Model):
            value = value.__class__

        if isinstance(value, type) and issubclass(value, models.Model):
            ct = ContentType.objects.get_for_model(value)
            return ct in self._registry

        return False

    def __iter__(self):
        return iter(self._registry)

@dataclass(frozen=True)
class BaseItemTypeDefinition:
    model: Type[models.Model]
    code: str
    name: str

NOTABLE_MODELS_REGISTRY = ModelRegistry()
