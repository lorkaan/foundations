from django.shortcuts import render
from ecosystem_foundations.watchdog.models import Signal, SignalItemType
from ecosystem_foundations.watchdog.serializers import SignalItemTypeSerializer, SignalSerializer
from rest_framework import viewsets
from ecosystem_foundations.base.views import ActiveQuerysetMixin, BaseItemTypeQueryViewSetMixin, BaseQueryViewSetMixin, TimeAuditableQuerysetMixin 

# Create your views here.
class SignalItemTypeViewSet(
    ActiveQuerysetMixin,
    BaseItemTypeQueryViewSetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = SignalItemType.objects.all()
    serializer_class = SignalItemTypeSerializer

class SignalViewSet(
    ActiveQuerysetMixin,
    TimeAuditableQuerysetMixin,
    BaseQueryViewSetMixin,
    viewsets.ModelViewSet,
):
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer