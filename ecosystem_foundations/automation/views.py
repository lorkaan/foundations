from django.shortcuts import render
from ecosystem_foundations.automation.models import AutomationAction, AutomationActionRun, AutomationRule, AutomationRun, AutomationTrigger
from ecosystem_foundations.automation.serializers import AutomationActionRunSerializer, AutomationActionSerializer, AutomationRuleSerializer, AutomationRunSerializer, AutomationTriggerSerializer
from ecosystem_foundations.base.views import ActiveQuerysetMixin, BaseQueryViewSetMixin, ForeignKeyFilterMixin, TimeAuditableQuerysetMixin
from rest_framework import viewsets

# Create your views here.

class RuleFilterMixin(ForeignKeyFilterMixin):
    fk_field = "rule"


class SignalTypeFilterMixin(ForeignKeyFilterMixin):
    fk_field = "signal_type"


class TriggerFilterMixin(ForeignKeyFilterMixin):
    fk_field = "trigger"


class QueryFilterMixin(ForeignKeyFilterMixin):
    fk_field = "query"

class RunFilterMixin(ForeignKeyFilterMixin):
    fk_field = "run"


class ActionFilterMixin(ForeignKeyFilterMixin):
    fk_field = "action"

class AutomationRuleQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset



class AutomationRuleViewSet(
    TimeAuditableQuerysetMixin,
    QueryFilterMixin,
    AutomationRuleQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = AutomationRule.objects.select_related("query")
    serializer_class = AutomationRuleSerializer

class AutomationTriggerQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        trigger_type = params.get("trigger_type")
        schedule = params.get("schedule")

        if trigger_type:
            queryset = queryset.filter(trigger_type=trigger_type)

        if schedule:
            queryset = queryset.filter(schedule=schedule)

        return queryset

class AutomationTriggerViewSet(
    ActiveQuerysetMixin,
    TimeAuditableQuerysetMixin,
    RuleFilterMixin,
    SignalTypeFilterMixin,
    AutomationTriggerQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = AutomationTrigger.objects.select_related(
        "rule",
        "signal_type",
    )
    serializer_class = AutomationTriggerSerializer

class AutomationActionQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        action_type = params.get("type")
        order = params.get("order")

        if action_type:
            queryset = queryset.filter(type=action_type)

        if order:
            queryset = queryset.filter(order=order)

        return queryset


class AutomationActionViewSet(
    ActiveQuerysetMixin,
    TimeAuditableQuerysetMixin,
    TriggerFilterMixin,
    AutomationActionQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = AutomationAction.objects.select_related("trigger")
    serializer_class = AutomationActionSerializer

class AutomationRunQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        status = params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset

class AutomationRunViewSet(
    TimeAuditableQuerysetMixin,
    TriggerFilterMixin,
    RuleFilterMixin,
    AutomationRunQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = AutomationRun.objects.select_related(
        "trigger",
        "rule",
    )
    serializer_class = AutomationRunSerializer

class AutomationActionRunQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset

class AutomationActionRunViewSet(
    RunFilterMixin,
    ActionFilterMixin,
    AutomationActionRunQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = AutomationActionRun.objects.select_related(
        "run",
        "action",
    )
    serializer_class = AutomationActionRunSerializer