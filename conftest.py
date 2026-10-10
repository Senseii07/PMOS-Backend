"""
Shared pytest fixtures for the Serene Wellness backend.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import AllowListEntry, Profile, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_user(db):
    """Factory — creates a User + Profile + AllowListEntry."""
    def _make(email="user@example.com", role=User.Role.PARTICIPANT, **kwargs):
        AllowListEntry.objects.get_or_create(email=email)
        password = kwargs.pop("password", "password123")
        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            is_allowlisted=True,
            **kwargs,
        )
        Profile.objects.get_or_create(user=user)
        return user

    return _make


@pytest.fixture
def participant(make_user):
    return make_user(email="participant@example.com")


@pytest.fixture
def admin_user(make_user):
    return make_user(email="admin@example.com", role=User.Role.ADMIN)


@pytest.fixture
def auth_client(api_client, participant):
    """APIClient pre-authenticated as the default participant."""
    refresh = RefreshToken.for_user(participant)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """APIClient pre-authenticated as the admin user."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client
