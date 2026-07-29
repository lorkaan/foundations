from django.shortcuts import render
from rest_framework import viewsets
from ..base.views import ActiveQuerysetMixin, BaseQueryViewSetMixin, TimeAuditableQuerysetMixin
from .models import GlobalParameter
from .serializers import GlobalParameterSerializer

# Create your views here.

class GlobalParameterQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        name = params.get("name")
        param_type = params.get("type")

        if name:
            queryset = queryset.filter(name__icontains=name)

        if param_type:
            queryset = queryset.filter(type=param_type)

        return queryset

class GlobalParameterViewSet(
    ActiveQuerysetMixin,
    TimeAuditableQuerysetMixin,
    GlobalParameterQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = GlobalParameter.objects.all()
    serializer_class = GlobalParameterSerializer