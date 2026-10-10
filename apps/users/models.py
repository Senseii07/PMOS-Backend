"""
Custom User model for Serene Wellness.

Extends AbstractUser to add Google OAuth fields, role, and allow-list flag.
Usernames are not used — email is the unique identifier.
"""
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Create users without a username field."""

    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        PARTICIPANT = "participant", "Participant"

    # Remove username — we identify by email
    username = None

    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    avatar_url = models.URLField(max_length=512, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)
    is_allowlisted = models.BooleanField(
        default=False,
        help_text="Only allow-listed users can access the app.",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # createsuperuser won't ask for username

    def __str__(self):
        return self.email

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN


class AllowListEntry(models.Model):
    """
    Stores invited email addresses.  Admin adds entries here;
    the OAuth callback checks this table before issuing a JWT.
    """
    email = models.EmailField(unique=True)
    added_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Allow-list entry"
        verbose_name_plural = "Allow-list entries"
        ordering = ["email"]

    def __str__(self):
        return self.email


class Profile(models.Model):
    class Sex(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT = "prefer_not_to_say", "Prefer not to say"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=20, choices=Sex.choices, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    health_goals = models.TextField(blank=True)
    conditions_notes = models.TextField(
        blank=True,
        help_text="Free-text; treated as sensitive health data.",
    )
    # Consent flags — must be True before storing sensitive logs
    consent_symptom_logging = models.BooleanField(default=False)
    consent_ai_context = models.BooleanField(
        default=False,
        help_text="Allow the AI assistant to reference this user's health logs.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.email})"
