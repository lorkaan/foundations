from django.shortcuts import render
from .models import Signal, SignalItemType
from .serializers import SignalItemTypeSerializer, SignalSerializer
from rest_framework import viewsets
from ..base.views import ActiveQuerysetMixin, BaseItemTypeQueryViewSetMixin, BaseQueryViewSetMixin, TimeAuditableQuerysetMixin 

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