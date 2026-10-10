from django.contrib import admin

from .models import AuditLog, MealLog, SymptomLog, WaterLog, WeightLog


@admin.register(MealLog)
class MealLogAdmin(admin.ModelAdmin):
    list_display = ("user", "food_query", "calories", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("food_query", "user__email")
    raw_id_fields = ("user",)
    date_hierarchy = "timestamp"


@admin.register(SymptomLog)
class SymptomLogAdmin(admin.ModelAdmin):
    list_display = ("user", "symptom", "severity", "timestamp")
    list_filter = ("severity", "timestamp")
    search_fields = ("symptom", "notes", "user__email")
    raw_id_fields = ("user",)
    date_hierarchy = "timestamp"


@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ("user", "amount_ml", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    date_hierarchy = "timestamp"


@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ("user", "weight_kg", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("notes", "user__email")
    raw_id_fields = ("user",)
    date_hierarchy = "timestamp"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("actor", "target_user", "action", "resource_type", "resource_id", "timestamp")
    list_filter = ("action", "resource_type", "timestamp")
    search_fields = ("actor__email", "target_user__email", "detail")
    raw_id_fields = ("actor", "target_user")
    date_hierarchy = "timestamp"
