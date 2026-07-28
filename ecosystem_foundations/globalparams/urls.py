from rest_framework.routers import DefaultRouter

from .views import (
    GlobalParameterViewSet
)

router = DefaultRouter()

router.register(r"parameters", GlobalParameterViewSet, basename="global-parameter")

urlpatterns = router.urls