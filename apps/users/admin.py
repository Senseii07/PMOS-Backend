from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AllowListEntry, Profile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "role", "is_allowlisted", "is_staff")
    list_filter = ("role", "is_allowlisted", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "avatar_url")}),
        ("Google OAuth", {"fields": ("google_id",)}),
        ("Access", {"fields": ("role", "is_allowlisted", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "is_allowlisted"),
            },
        ),
    )


@admin.register(AllowListEntry)
class AllowListEntryAdmin(admin.ModelAdmin):
    list_display = ("email", "added_at", "note")
    search_fields = ("email",)
    ordering = ("email",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "sex", "consent_symptom_logging", "consent_ai_context")
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
