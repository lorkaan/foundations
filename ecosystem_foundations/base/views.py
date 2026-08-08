from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from .constants import ActiveState, ComparisonOperator, SystemState
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers

# Create your views here.

class BaseQueryViewSetMixin:

    def get_base_queryset(self):
        return super().get_queryset()

    # Each child of this function must have the following line:
    #   queryset = super().apply_queryset_filters(queryset)
    def apply_filtering(self, queryset):
        return queryset

    def get_queryset(self):
            queryset = self.get_base_queryset()
            return self.apply_filtering(queryset)


class ActiveQuerysetMixin(BaseQueryViewSetMixin):

    def _get_state(self):
        raw = self.request.query_params.get(
            "state",
            ActiveState.ACTIVE
        )

        try:
            return ActiveState(str(raw).lower())
        except ValueError:
            return ActiveState.ACTIVE

    def filter_by_state(self, queryset):
        if not hasattr(queryset.model, "is_active"):
            raise TypeError(
                "ActiveModelViewSet requires a model using ActiveMixin"
            )
        
        state = self._get_state()

        if state == ActiveState.INACTIVE:
            return queryset.filter(is_active=False)

        if state == ActiveState.ALL:
            return queryset

        return queryset.filter(is_active=True)

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)
        return self.filter_by_state(queryset)
        

class TimeAuditableQuerysetMixin(BaseQueryViewSetMixin):

    FILTERABLE_TIMESTAMP_FIELDS = {
        "created_at",
        "updated_at",
    }

    def get_time_filter_value(self, field):
        """
        Builds a Django filter expression for a timestamp field.
        """

        params = self.request.query_params
        filters = {}

        # Comparison filters
        for operator, lookup in {
            ComparisonOperator.EQ: "",
            ComparisonOperator.LT: "__lt",
            ComparisonOperator.LTE: "__lte",
            ComparisonOperator.GT: "__gt",
            ComparisonOperator.GTE: "__gte",
        }.items():

            key = f"{field}_{operator.value}"

            if key in params:
                filters[f"{field}{lookup}"] = params[key]

        # Range filters
        start = params.get(f"{field}_start")
        end = params.get(f"{field}_end")

        if start:
            filters[f"{field}__gte"] = start

        if end:
            filters[f"{field}__lte"] = end

        return filters

    def filter_by_time_audit(self, queryset):
        filters = {}

        for field in self.FILTERABLE_TIMESTAMP_FIELDS:
            filters.update(
                self.get_time_filter_value(field)
            )

        if filters:
            queryset = queryset.filter(**filters)

        return queryset

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)
        return self.filter_by_time_audit(queryset)

class IsSystemQuerysetMixin(BaseQueryViewSetMixin):

    def _get_system_state(self):
        raw = self.request.query_params.get(
            "system",
            SystemState.NON_SYSTEM
        )

        try:
            return SystemState(str(raw).lower())
        except ValueError:
            return SystemState.NON_SYSTEM

    def apply_queryset_filters(self, queryset):
        queryset = super().apply_queryset_filters(queryset)

        state = self._get_system_state()

        if state == SystemState.SYSTEM:
            return queryset.filter(is_system=True)

        if state == SystemState.ALL:
            return queryset

        return queryset.filter(is_system=False)

class BaseItemTypeQueryViewSetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        code = params.get("code")
        name = params.get("name")

        if code:
            queryset = queryset.filter(code=code)

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset

class RunStatusQueryViewSetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        status = self.request.query_params.get("status")

        if not status:
            return queryset

        valid_statuses = {
            choice[0]
            for choice in queryset.model.RunStatus.choices
        }

        if status not in valid_statuses:
            return queryset.none()

        return queryset.filter(status=status)


class GenericTargetQuerysetMixin(BaseQueryViewSetMixin):

    def _parse_target(self):
        """
        Supports:
        - target.model + target.id
        - OR target="app_label.model:uuid"
        """

        params = self.request.query_params

        # Option 1: split params
        model = params.get("target.model")
        object_id = params.get("target.id")

        if model and object_id:
            return model, object_id

        # Option 2: compact form
        raw = params.get("target")
        if raw:
            try:
                model, object_id = raw.split(":")
                return model, object_id
            except ValueError:
                return None, None

        return None, None

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        model, object_id = self._parse_target()

        if not model or not object_id:
            return queryset

        try:
            app_label, model_name = model.split(".")
            content_type = ContentType.objects.get(
                app_label=app_label,
                model=model_name
            )
        except (ValueError, ContentType.DoesNotExist):
            return queryset.none()

        return queryset.filter(
            content_type=content_type,
            object_id=object_id
        )

class ContentTypeQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        model_param = self.request.query_params.get("model")

        if not model_param:
            return queryset

        try:
            app_label, model = model_param.split(".")
            content_type = ContentType.objects.get(
                app_label=app_label,
                model=model
            )
        except (ValueError, ContentType.DoesNotExist):
            return queryset.none()

        return queryset.filter(content_type=content_type)

class ForeignKeyFilterMixin(BaseQueryViewSetMixin):

    fk_field = None
    query_param = None  # optional override

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        if not self.fk_field:
            return queryset

        param = self.query_param or f"{self.fk_field}_id"
        value = self.request.query_params.get(param)

        if value:
            queryset = queryset.filter(**{f"{self.fk_field}_id": value})

        return queryset

"""
    A Mixin in Schema to expose the Fliter Schema for any given data viewset.

    This will allow the frontend to dynamically build UIs for filtering on a single
    viewset. This is very different from the Stored Query app that enables much more
    advanced querying and is useful for a Dashboard. This is designed for specific 
    pages that seek to isolate a specific data model and perform basic queries over that
    model, such as an Events page.
"""
class FilterSchemaMixin:
    """
    Mixin to expose filter schema for a ViewSet.

    Uses:
    - serializer → field typing
    - filterset_fields → what is filterable
    """

    RELATION_OPTION_CONFIG = {
        # model_name: (value_field, label_field)
        # "EventScheduleItemType": ("id", "name"),
    }

    LOOKUP_META = {
        "exact": {
            "label": "equals",
            "operator": "=",
        },
        "gte": {
            "label": "after",
            "operator": ">=",
        },
        "lte": {
            "label": "before",
            "operator": "<=",
        },
        "icontains": {
            "label": "contains",
            "operator": "like",
        },
    }

    FILTER_TYPE_MAP = {
        serializers.CharField: "string",
        serializers.TextField: "string",
        serializers.IntegerField: "number",
        serializers.FloatField: "number",
        serializers.BooleanField: "boolean",
        serializers.DateField: "date",
        serializers.DateTimeField: "datetime",
        serializers.UUIDField: "uuid",
    }

    MAX_INLINE_OPTIONS = 50

    def _get_lookup_meta(self, lookup):
        return self.LOOKUP_META.get(lookup, {
            "label": lookup,
            "operator": lookup,
        })

    def _get_relation_config(self, model):
        """
        Determine which fields to use for value/label
        """

        config = getattr(self, "RELATION_OPTION_CONFIG", {})

        if model.__name__ in config:
            return config[model.__name__]

        # ---- Smart defaults ----

        field_names = {f.name for f in model._meta.fields}

        # value priority
        if "id" in field_names:
            value_field = "id"
        elif "pk" in field_names:
            value_field = "pk"
        elif "code" in field_names:
            value_field = "code"
        else:
            value_field = next(iter(field_names))

        # label priority
        for candidate in ["name", "title", "label", "code"]:
            if candidate in field_names:
                label_field = candidate
                break
        else:
            label_field = value_field

        return value_field, label_field

    def _get_relation_options(self, model):
        """
        Return dropdown options if dataset is small enough
        """
        qs = model.objects.all()

        if qs[:self.MAX_INLINE_OPTIONS + 1].count() > self.MAX_INLINE_OPTIONS:
            return None

        value_field, label_field = self._get_relation_config(model)

        results = []

        for obj in qs:
            results.append({
                "value": getattr(obj, value_field, None),
                "label": getattr(obj, label_field, str(obj)),
            })

        return results

    def _get_filterset_fields(self):
        """
        Normalize filterset_fields into dict form:
        {
            "field": ["exact", "gte"]
        }
        """
        fields = getattr(self, "filterset_fields", {})

        if isinstance(fields, list):
            return {f: ["exact"] for f in fields}

        return fields

    def _expand_filters(self, filterset_fields):
        """
        Expand into:
        [
            ("type", "exact", "type"),
            ("start_time", "gte", "start_time__gte"),
        ]
        """
        expanded = []

        for field, lookups in filterset_fields.items():
            for lookup in lookups:
                name = field if lookup == "exact" else f"{field}__{lookup}"
                expanded.append((field, lookup, name))

        return expanded

    def _get_serializer_field(self, serializer, field_name):
        """
        Get top-level serializer field
        """
        return serializer.fields.get(field_name)

    def _resolve_relation_model(self, field):
        """
        Determine related model if this is a relation
        """
        # Nested serializer
        if isinstance(field, serializers.BaseSerializer):
            meta = getattr(field, "Meta", None)
            return getattr(meta, "model", None)

        # PK or Slug related field
        if hasattr(field, "queryset") and field.queryset is not None:
            return field.queryset.model

        return None

    def _map_field_type(self, field, model=None, sub_field=None):
        """
        Determine UI type
        """
        # Relation
        if isinstance(field, serializers.BaseSerializer):
            return "relation"

        if hasattr(field, "queryset"):
            return "relation"

        # Primitive types
        for cls, label in self.FILTER_TYPE_MAP.items():
            if isinstance(field, cls):
                return label

        # Fallback
        return "string"

    def _build_field_schema(self, serializer, base_field, lookup, name):
        """
        Build schema for a single filter field
        """
        parts = base_field.split("__")
        root_field_name = parts[0]

        field = self._get_serializer_field(serializer, root_field_name)

        if not field:
            return None

        lookup_meta = self._get_lookup_meta(lookup)
        schema = {
            "name": name,
            "base": base_field,
            "lookup": lookup,
            "lookup_label": lookup_meta["label"],
            "operator": lookup_meta["operator"],
        }

        # Detect relation
        model = self._resolve_relation_model(field)

        if model:
            options = self._get_relation_options(model)

            schema.update({
                "type": "relation",
                "model": model.__name__,
                "endpoint": f"/{model._meta.model_name}s/",
                "has_inline_options": options is not None,
            })

            # Only include options if they exist
            if options is not None:
                schema["options"] = options

            # Handle traversal (type__code)
            if len(parts) > 1:
                sub_field = parts[1]
                try:
                    model_field = model._meta.get_field(sub_field)
                    schema["sub_type"] = model_field.get_internal_type()
                except Exception:
                    schema["sub_type"] = "unknown"

        else:
            schema["type"] = self._map_field_type(field)

        return schema

    @action(detail=False, methods=["get"], url_path="filter-schema")
    def filter_schema(self, request):
        serializer = self.get_serializer()
        filterset_fields = self._get_filterset_fields()
        expanded = self._expand_filters(filterset_fields)

        fields = []

        for base, lookup, name in expanded:
            schema = self._build_field_schema(serializer, base, lookup, name)
            if schema:
                fields.append(schema)

        return Response({
            "filters": fields
        })