"""
Serializers for the conditions app.
"""
from rest_framework import serializers
from .models import ConditionEntry, MediaAsset


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = ["id", "media_type", "url", "caption", "attribution", "order"]
        read_only_fields = ["id"]


class ConditionEntrySerializer(serializers.ModelSerializer):
    media_assets = MediaAssetSerializer(many=True, read_only=True)

    class Meta:
        model = ConditionEntry
        fields = [
            "id",
            "name",
            "slug",
            "summary",
            "prevention_tips",
            "source_refs",
            "is_published",
            "created_at",
            "updated_at",
            "media_assets",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
