"""
Serializers for the health tracking app.
"""
from rest_framework import serializers
from .models import AuditLog, MealLog, SymptomLog, WaterLog, WeightLog


class MealLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealLog
        fields = [
            "id",
            "timestamp",
            "food_query",
            "edamam_response",
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "fiber_g",
            "created_at",
        ]
        read_only_fields = ["id", "edamam_response", "calories", "protein_g",
                            "carbs_g", "fat_g", "fiber_g", "created_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field_name in ("calories", "protein_g", "carbs_g", "fat_g", "fiber_g"):
            value = data.get(field_name)
            if value is not None:
                data[field_name] = float(value)
        return data


class MealLogCreateSerializer(serializers.Serializer):
    """Used on creation — only the food query is submitted; the backend calls Edamam."""
    food_query = serializers.CharField(max_length=500)
    timestamp = serializers.DateTimeField()


class SymptomLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymptomLog
        fields = ["id", "timestamp", "symptom", "severity", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class WaterLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLog
        fields = ["id", "timestamp", "amount_ml", "created_at"]
        read_only_fields = ["id", "created_at"]


class WeightLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightLog
        fields = ["id", "timestamp", "weight_kg", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "actor", "target_user", "action", "resource_type",
                  "resource_id", "detail", "timestamp"]
        read_only_fields = fields
