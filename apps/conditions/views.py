"""
Views for the conditions app.
"""
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.users.permissions import IsAdminRole

from .models import ConditionEntry, MediaAsset
from .serializers import ConditionEntrySerializer, MediaAssetSerializer


class ConditionEntryViewSet(viewsets.ModelViewSet):
    """
    list   GET  /api/conditions/          — all published entries (participants)
    detail GET  /api/conditions/<slug>/   — single entry
    write  POST/PATCH/DELETE              — admin only
    """

    queryset = ConditionEntry.objects.prefetch_related("media_assets").order_by("name")
    serializer_class = ConditionEntrySerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "summary"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Non-admins only see published entries
        if not (self.request.user.is_authenticated and self.request.user.role == "admin"):
            qs = qs.filter(is_published=True)
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]


class MediaAssetViewSet(viewsets.ModelViewSet):
    """Admin-managed media assets nested under conditions."""

    queryset = MediaAsset.objects.select_related("condition").order_by("condition", "order")
    serializer_class = MediaAssetSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]
