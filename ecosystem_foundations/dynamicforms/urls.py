from rest_framework.routers import DefaultRouter
from .views import FormTypeViewSet, FormInstanceViewSet, FormQuestionViewSet

router = DefaultRouter()
router.register(r"form-types", FormTypeViewSet)
router.register(r"form-instances", FormInstanceViewSet)
router.register(r"form-questions", FormQuestionViewSet)

urlpatterns = router.urls