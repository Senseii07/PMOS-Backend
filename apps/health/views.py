"""
Views for health tracking — MealLog, SymptomLog, WaterLog, WeightLog.

All endpoints are scoped to the authenticated user.
Admins can read any user's data via the admin-only aggregate endpoints.
"""
import logging

import requests as http_requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdminRole

from .models import AuditLog, MealLog, SymptomLog, WaterLog, WeightLog
from .serializers import (
    MealLogCreateSerializer,
    MealLogSerializer,
    SymptomLogSerializer,
    WaterLogSerializer,
    WeightLogSerializer,
)

logger = logging.getLogger(__name__)


def _write_audit(actor, target_user, action, resource_type, resource_id=None, detail=""):
    """Write an AuditLog entry without crashing the main request."""
    try:
        AuditLog.objects.create(
            actor=actor,
            target_user=target_user,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to write audit log: %s", exc)


class MealLogListCreateView(generics.ListCreateAPIView):
    """GET list / POST create meal logs. POST calls Edamam server-side."""

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MealLogCreateSerializer
        return MealLogSerializer

    def get_queryset(self):
        return MealLog.objects.filter(user=self.request.user).order_by("-timestamp")

    def create(self, request, *args, **kwargs):
        serializer = MealLogCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        food_query = serializer.validated_data["food_query"]
        timestamp = serializer.validated_data["timestamp"]

        edamam_data = {}
        calories = protein = carbs = fat = fiber = None

        try:
            resp = http_requests.post(
                "https://api.edamam.com/api/nutrition-details",
                params={"app_id": settings.EDAMAM_APP_ID, "app_key": settings.EDAMAM_APP_KEY},
                json={"title": food_query, "ingr": [food_query]},
                timeout=10,
            )
            resp.raise_for_status()
            edamam_data = resp.json()
            nutrients = edamam_data.get("totalNutrients", {})
            calories = edamam_data.get("calories")
            protein = nutrients.get("PROCNT", {}).get("quantity")
            carbs = nutrients.get("CHOCDF", {}).get("quantity")
            fat = nutrients.get("FAT", {}).get("quantity")
            fiber = nutrients.get("FIBTG", {}).get("quantity")
        except http_requests.exceptions.Timeout:
            logger.warning("Edamam timeout for: %s", food_query)
        except http_requests.exceptions.HTTPError as exc:
            logger.warning("Edamam HTTP error: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("Edamam unexpected error: %s", exc)

        meal_log = MealLog.objects.create(
            user=request.user,
            timestamp=timestamp,
            food_query=food_query,
            edamam_response=edamam_data,
            calories=calories,
            protein_g=protein,
            carbs_g=carbs,
            fat_g=fat,
            fiber_g=fiber,
        )
        return Response(MealLogSerializer(meal_log).data, status=status.HTTP_201_CREATED)


class MealLogDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = MealLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealLog.objects.filter(user=self.request.user)


class SymptomLogListCreateView(generics.ListCreateAPIView):
    serializer_class = SymptomLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SymptomLog.objects.filter(user=self.request.user).order_by("-timestamp")

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        user = self.request.user
        profile = getattr(user, "profile", None)
        if not profile or not profile.consent_symptom_logging:
            raise PermissionDenied(
                "Enable symptom logging consent in your profile before logging symptoms."
            )
        instance = serializer.save(user=user)
        _write_audit(user, user, AuditLog.Action.CREATE, "SymptomLog", instance.pk)


class SymptomLogDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = SymptomLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SymptomLog.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        _write_audit(request.user, instance.user, AuditLog.Action.READ, "SymptomLog", instance.pk)
        return super().retrieve(request, *args, **kwargs)


class WaterLogListCreateView(generics.ListCreateAPIView):
    serializer_class = WaterLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WaterLog.objects.filter(user=self.request.user).order_by("-timestamp")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WeightLogListCreateView(generics.ListCreateAPIView):
    serializer_class = WeightLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WeightLog.objects.filter(user=self.request.user).order_by("-timestamp")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AdminHealthSummaryView(APIView):
    """GET /api/health/admin/summary/ — anonymised aggregate stats."""

    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        from django.db.models import Avg, Count
        return Response({
            "total_meal_logs": MealLog.objects.count(),
            "total_symptom_logs": SymptomLog.objects.count(),
            "avg_calories_per_log": MealLog.objects.aggregate(avg=Avg("calories"))["avg"],
            "symptom_distribution": list(
                SymptomLog.objects.values("symptom")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            ),
        })

