from rest_framework.routers import DefaultRouter

from .views import ConditionEntryViewSet, MediaAssetViewSet

router = DefaultRouter()
router.register(r"", ConditionEntryViewSet, basename="condition")
router.register(r"media", MediaAssetViewSet, basename="media-asset")

urlpatterns = router.urls
