from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CampaignViewSet,
    DailyTaskViewSet,
    TaskCompletionViewSet,
)

router = DefaultRouter()
router.register(r"", CampaignViewSet, basename="campaign")
router.register(r"tasks", DailyTaskViewSet, basename="daily-task")
router.register(r"completions", TaskCompletionViewSet, basename="task-completion")

urlpatterns = router.urls
