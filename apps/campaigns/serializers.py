"""
Serializers for the campaigns app.
"""
from rest_framework import serializers
from .models import Campaign, CampaignEnrollment, DailyTask, TaskCompletion


class DailyTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyTask
        fields = ["id", "campaign", "day_number", "title", "description", "tips"]
        read_only_fields = ["id"]


class TaskCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCompletion
        fields = ["id", "user", "task", "completed_at", "notes"]
        read_only_fields = ["id", "user", "completed_at"]


class CampaignEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignEnrollment
        fields = ["id", "user", "campaign", "joined_at", "status"]
        read_only_fields = ["id", "user", "joined_at"]


class CampaignSerializer(serializers.ModelSerializer):
    daily_tasks = DailyTaskSerializer(many=True, read_only=True)
    enrollment_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "title",
            "description",
            "start_date",
            "end_date",
            "status",
            "target_metrics",
            "created_by",
            "created_at",
            "updated_at",
            "daily_tasks",
            "enrollment_count",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_enrollment_count(self, obj):
        return obj.enrollments.filter(status="active").count()
