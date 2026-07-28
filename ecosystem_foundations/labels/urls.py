from rest_framework.routers import DefaultRouter

from .views import (
    ModelFieldLabelViewSet
)

router = DefaultRouter()

router.register(r"", ModelFieldLabelViewSet, basename="model-field-label")

urlpatterns = router.urls