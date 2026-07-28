from django.shortcuts import render
from ecosystem_foundations.labels.models import ModelFieldLabel
from ecosystem_foundations.labels.serializers import ModelFieldLabelSerializer
from rest_framework import viewsets
from ecosystem_foundations.base.views import BaseQueryViewSetMixin, ContentTypeQuerysetMixin

# Create your views here.
class ModelFieldLabelQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        field_path = params.get("field_path")
        group = params.get("group")

        if field_path:
            queryset = queryset.filter(field_path=field_path)

        if group:
            queryset = queryset.filter(group__icontains=group)

        return queryset

class ModelFieldLabelViewSet(
    ContentTypeQuerysetMixin,
    ModelFieldLabelQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = ModelFieldLabel.objects.select_related(
        "content_type"
    )
    serializer_class = ModelFieldLabelSerializer