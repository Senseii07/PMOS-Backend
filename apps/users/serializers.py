"""
Serializers for the users app.
"""
from rest_framework import serializers
from .models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "age",
            "sex",
            "height_cm",
            "weight_kg",
            "health_goals",
            "conditions_notes",
            "consent_symptom_logging",
            "consent_ai_context",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar_url",
            "role",
            "is_allowlisted",
            "profile",
        ]
        read_only_fields = ["id", "email", "role", "is_allowlisted"]


class GoogleAuthSerializer(serializers.Serializer):
    """Accepts the Google ID token from the frontend."""
    id_token = serializers.CharField()
