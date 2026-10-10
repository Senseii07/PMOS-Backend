from django.contrib import admin

from .models import ConditionEntry, MediaAsset


@admin.register(ConditionEntry)
class ConditionEntryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_published", "created_at", "updated_at")
    list_filter = ("is_published", "created_at", "updated_at")
    search_fields = ("name", "summary")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("condition", "media_type", "url", "order", "created_at")
    list_filter = ("media_type", "condition", "created_at")
    search_fields = ("caption", "attribution", "condition__name")
    raw_id_fields = ("condition",)
    ordering = ("condition", "order")
