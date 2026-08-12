from django.shortcuts import render

from ..labels.services import get_field_label

from .services.queryAstHandler import AnnotatedQueryAstHandler
from .models import SavedQuery, SavedQueryPermission
from .serializers import SavedQueryPermissionSerializer, SavedQuerySerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
import csv

from ..base.views import ActiveQuerysetMixin, BaseQueryViewSetMixin, ContentTypeQuerysetMixin, ForeignKeyFilterMixin, IsSystemQuerysetMixin, TimeAuditableQuerysetMixin

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

    def execute_query(
        self,
        request,
        post_flag=True,
        query_result_return=False,
    ):
        query = self.get_object()

        if post_flag:
            data = request.data
        else:
            data = request.query_params

        params = data.get("params", {})

        extra_options = {
            "order_by": data.get("order_by"),
            "limit": data.get("limit"),
            "filters": data.get("filters"),
        }

        query_results = AnnotatedQueryAstHandler.run(
            query.to_ast_payload(),
            params,
            annotateFlag=not query_result_return,
        )

        qs = self.__class__.apply_extra_options(
            query_results,
            extra_options,
        )

        if query_result_return:
            return qs

        virtual_fields = getattr(qs, "_virtual_fields", [])

        objects = list(qs)
        new_data = list(qs.values())

        if virtual_fields:
            new_data = AnnotatedQueryAstHandler.apply_virtual_fields(
                new_data,
                objects,
                virtual_fields,
            )

        return new_data

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="run",
    )
    def run(self, request, pk=None):
        rows = self.execute_query(
            request,
            post_flag=request.method == "POST",
        )

        return Response({
            "results": rows,
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="download",
    )
    def download(self, request, pk=None):
        rows = self.execute_query(
            request,
            post_flag=True,
        )

        if not isinstance(rows, list):
            return HttpResponse(status=404)

        if not rows:
            return HttpResponse(
                "No results",
                status=404,
                content_type="text/plain",
            )

        name = request.data.get(
            "name",
            "Untitled",
        )

        timestamp = timezone.localtime().strftime(
            "%Y%m%d_%H%M%S"
        )

        field_labels_override = request.data.get(
            "field_labels",
            {},
        )

        selected_fields = request.data.get(
            "selected_fields",
            [],
        )

        if not isinstance(selected_fields, list):
            selected_fields = list(rows[0].keys())

        model_class = self.get_object().get_model_class()

        headers = [
            get_field_label(
                model_class,
                field,
                override=field_labels_override,
            )
            for field in selected_fields
        ]

        response = HttpResponse(
            content_type="text/csv",
        )

        filename = (
            f"{self.sanitize_filename(name)}_"
            f"{timestamp}.csv"
        )

        response["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

        writer = csv.writer(response)

        writer.writerow(headers)

        for row in rows:
            writer.writerow([
                row.get(field, "")
                for field in selected_fields
            ])

        return response