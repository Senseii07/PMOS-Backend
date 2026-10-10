"""
Views for the campaigns app.
"""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsAdminRole

from .models import Campaign, CampaignEnrollment, DailyTask, TaskCompletion
from .serializers import (
    CampaignEnrollmentSerializer,
    CampaignSerializer,
    DailyTaskSerializer,
    TaskCompletionSerializer,
)


class CampaignViewSet(viewsets.ModelViewSet):
    """
    Admin: full CRUD.
    Participant: list + retrieve active/completed campaigns.
    """

    queryset = Campaign.objects.prefetch_related("daily_tasks").order_by("-start_date")
    serializer_class = CampaignSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """POST /api/campaigns/<pk>/enroll/ — join a campaign."""
        campaign = self.get_object()
        enrollment, created = CampaignEnrollment.objects.get_or_create(
            user=request.user,
            campaign=campaign,
        )
        if not created and enrollment.status == CampaignEnrollment.EnrollmentStatus.DROPPED:
            enrollment.status = CampaignEnrollment.EnrollmentStatus.ACTIVE
            enrollment.save(update_fields=["status"])
        return Response(
            CampaignEnrollmentSerializer(enrollment).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def my_progress(self, request, pk=None):
        """GET /api/campaigns/<pk>/my_progress/ — tasks + completion status."""
        campaign = self.get_object()
        tasks = DailyTask.objects.filter(campaign=campaign)
        completed_ids = set(
            TaskCompletion.objects.filter(
                user=request.user,
                task__campaign=campaign,
            ).values_list("task_id", flat=True)
        )
        data = []
        for task in tasks:
            d = DailyTaskSerializer(task).data
            d["completed"] = task.id in completed_ids
            data.append(d)
        return Response(data)


class DailyTaskViewSet(viewsets.ModelViewSet):
    queryset = DailyTask.objects.select_related("campaign").order_by("campaign", "day_number")
    serializer_class = DailyTaskSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]


class TaskCompletionViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCompletionSerializer

    def get_queryset(self):
        return TaskCompletion.objects.filter(user=self.request.user).select_related("task")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        return [IsAuthenticated()]
