from django.shortcuts import render
from ecosystem_foundations.storedquery.models import SavedQuery, SavedQueryPermission
from ecosystem_foundations.storedquery.serializers import SavedQueryPermissionSerializer, SavedQuerySerializer
from rest_framework import viewsets

from ecosystem_foundations.base.views import ActiveQuerysetMixin, BaseQueryViewSetMixin, ContentTypeQuerysetMixin, ForeignKeyFilterMixin, IsSystemQuerysetMixin, TimeAuditableQuerysetMixin

# Create your views here.
class SavedQueryPermissionQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        user_id = params.get("user_id")
        role_id = params.get("role_id")
        level = params.get("level")

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if role_id:
            queryset = queryset.filter(role_id=role_id)

        if level:
            queryset = queryset.filter(level=level)

        return queryset


class SavedQueryPermissionViewSet(
    ActiveQuerysetMixin,              # only if model has ActiveMixin
    TimeAuditableQuerysetMixin,       # only if model has it
    SavedQueryPermissionQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = SavedQueryPermission.objects.select_related(
        "user",
        "role",
    )
    serializer_class = SavedQueryPermissionSerializer

class OwnerFilterMixin(ForeignKeyFilterMixin):
    fk_field = "owner"

class SavedQueryViewSet(
    TimeAuditableQuerysetMixin,
    ContentTypeQuerysetMixin,
    OwnerFilterMixin,
    IsSystemQuerysetMixin,  # if you created it
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = SavedQuery.objects.select_related(
        "owner",
        "content_type",
    ).prefetch_related(
        "permissions__user",
        "permissions__role",
    )

    serializer_class = SavedQuerySerializer