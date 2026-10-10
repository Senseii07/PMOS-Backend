"""
Models for the condition/illness information hub.
"""
from django.db import models


class ConditionEntry(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    summary = models.TextField()
    prevention_tips = models.TextField(blank=True)
    # Optional structured clinical reference data (e.g. FHIR codes)
    source_refs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured reference data (SNOMED codes, ICD codes, etc.).",
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Condition entry"
        verbose_name_plural = "Condition entries"

    def __str__(self):
        return self.name


class MediaAsset(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"

    condition = models.ForeignKey(
        ConditionEntry,
        on_delete=models.CASCADE,
        related_name="media_assets",
    )
    media_type = models.CharField(max_length=10, choices=MediaType.choices)
    url = models.URLField(max_length=1024)
    caption = models.CharField(max_length=500, blank=True)
    # Attribution is mandatory — all health campaign media must be properly licensed
    attribution = models.CharField(
        max_length=500,
        help_text="License and attribution text for this asset.",
    )
    order = models.PositiveSmallIntegerField(default=0, help_text="Display order within the condition")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["condition", "order"]

    def __str__(self):
        return f"{self.media_type} for {self.condition.name}"
