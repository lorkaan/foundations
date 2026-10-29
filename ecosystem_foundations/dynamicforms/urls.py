from rest_framework.routers import DefaultRouter
from .views import FormGroupInstanceTreeViewSet, FormGroupInstanceViewSet, FormGroupInstanceWriteViewSet, FormTypeViewSet, FormInstanceViewSet, FormQuestionViewSet

router = DefaultRouter()
router.register(r"form-types", FormTypeViewSet)
router.register(r"form-instances", FormInstanceViewSet)
router.register(r"form-questions", FormQuestionViewSet)
router.register(r"group-instances", FormGroupInstanceViewSet)
router.register(r"group-instances-tree", FormGroupInstanceTreeViewSet, basename="group-instance-tree")
router.register(r"group-instances-write", FormGroupInstanceWriteViewSet)

urlpatterns = router.urls