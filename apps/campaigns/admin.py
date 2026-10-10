from django.contrib import admin

from .models import Campaign, CampaignEnrollment, DailyTask, TaskCompletion


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "start_date", "end_date", "created_at")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("title", "description")
    date_hierarchy = "start_date"


@admin.register(CampaignEnrollment)
class CampaignEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "campaign", "status", "joined_at")
    list_filter = ("status", "joined_at")
    search_fields = ("user__email", "campaign__title")
    raw_id_fields = ("user", "campaign")


@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ("campaign", "day_number", "title")
    list_filter = ("campaign",)
    search_fields = ("title", "description")
    ordering = ("campaign", "day_number")
    raw_id_fields = ("campaign",)


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "task", "completed_at")
    list_filter = ("completed_at",)
    search_fields = ("user__email", "task__title")
    raw_id_fields = ("user", "task")
