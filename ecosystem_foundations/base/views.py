from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from .constants import ActiveState, ComparisonOperator, SystemState

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