"""
Models for health tracking (meals, symptoms, water, weight).
"""
from django.conf import settings
from django.db import models


class MealLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meal_logs",
    )
    timestamp = models.DateTimeField()
    food_query = models.CharField(max_length=500)
    # Full Edamam API response cached here to avoid repeated calls
    edamam_response = models.JSONField(default=dict)
    # Denormalised summary fields for quick queries
    calories = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    protein_g = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    carbs_g = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    fat_g = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    fiber_g = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.email} | {self.food_query} @ {self.timestamp:%Y-%m-%d %H:%M}"


class SymptomLog(models.Model):
    class Severity(models.IntegerChoices):
        MILD = 1, "Mild"
        MODERATE = 2, "Moderate"
        SEVERE = 3, "Severe"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="symptom_logs",
    )
    timestamp = models.DateTimeField()
    symptom = models.CharField(max_length=200)
    severity = models.PositiveSmallIntegerField(choices=Severity.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.email} | {self.symptom} (severity {self.severity})"


class WaterLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="water_logs",
    )
    timestamp = models.DateTimeField()
    amount_ml = models.PositiveIntegerField(help_text="Amount in millilitres")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.email} | {self.amount_ml} ml @ {self.timestamp:%Y-%m-%d}"


class WeightLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="weight_logs",
    )
    timestamp = models.DateTimeField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user.email} | {self.weight_kg} kg @ {self.timestamp:%Y-%m-%d}"


class AuditLog(models.Model):
    """
    Records access or mutation of sensitive health data.
    Written by views whenever SymptomLog or ChatMessage is
    created or read by someone other than the owning user.
    """

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        READ = "read", "Read"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_actions",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_targets",
    )
    action = models.CharField(max_length=10, choices=Action.choices)
    resource_type = models.CharField(max_length=100)
    resource_id = models.PositiveBigIntegerField(null=True, blank=True)
    detail = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.actor} {self.action} {self.resource_type}#{self.resource_id}"
