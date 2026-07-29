from django.shortcuts import render
from .models import RoleFieldPermission, UserFieldPermission
from .serializers import RoleFieldPermissionSerializer, UserFieldPermissionSerializer
from rest_framework import viewsets
from ..base.views import BaseQueryViewSetMixin, ContentTypeQuerysetMixin, ForeignKeyFilterMixin

# Create your views here.
class FieldPermissionQuerysetMixin(BaseQueryViewSetMixin):

    def apply_filtering(self, queryset):
        queryset = super().apply_filtering(queryset)

        params = self.request.query_params

        field_name = params.get("field_name")
        permission = params.get("permission")

        if field_name:
            queryset = queryset.filter(field_name=field_name)

        if permission:
            queryset = queryset.filter(permission=permission)

        return queryset

class RoleFilterQuerysetMixin(ForeignKeyFilterMixin):
    fk_field = "role"

class UserFilterQuerysetMixin(ForeignKeyFilterMixin):
    fk_field = "user"

class RoleFieldPermissionViewSet(
    ContentTypeQuerysetMixin,
    RoleFilterQuerysetMixin,
    FieldPermissionQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = RoleFieldPermission.objects.select_related(
        "role",
        "content_type",
    )
    serializer_class = RoleFieldPermissionSerializer

class UserFieldPermissionViewSet(
    ContentTypeQuerysetMixin,
    UserFilterQuerysetMixin,
    FieldPermissionQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = UserFieldPermission.objects.select_related(
        "user",
        "content_type",
    )
    serializer_class = UserFieldPermissionSerializer