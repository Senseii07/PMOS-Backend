"""
Tests for the user auth endpoints:
  POST /api/auth/google/
  GET  /api/auth/me/
  GET/PATCH /api/auth/profile/
"""
import pytest
from unittest.mock import MagicMock, patch
from django.urls import reverse

from apps.users.models import AllowListEntry, Profile, User


@pytest.mark.django_db
class TestGoogleAuthView:
    URL = "/api/auth/google/"

    def test_rejects_missing_token(self, api_client):
        resp = api_client.post(self.URL, {}, format="json")
        assert resp.status_code == 400

    def test_rejects_invalid_google_token(self, api_client):
        with patch(
            "apps.users.views.google_id_token.verify_oauth2_token",
            side_effect=ValueError("bad token"),
        ):
            resp = api_client.post(
                self.URL, {"id_token": "bad"}, format="json"
            )
        assert resp.status_code == 401

    def test_rejects_non_allowlisted_email(self, api_client):
        fake_info = {
            "sub": "google-123",
            "email": "stranger@example.com",
            "given_name": "Jane",
            "family_name": "Doe",
        }
        with patch(
            "apps.users.views.google_id_token.verify_oauth2_token",
            return_value=fake_info,
        ):
            resp = api_client.post(
                self.URL, {"id_token": "valid-token"}, format="json"
            )
        assert resp.status_code == 403
        assert resp.data["detail"] == "not_invited"

    def test_issues_jwt_for_allowlisted_email(self, api_client, db):
        email = "invited@example.com"
        AllowListEntry.objects.create(email=email)
        fake_info = {
            "sub": "google-456",
            "email": email,
            "given_name": "Alice",
            "family_name": "Smith",
            "picture": "https://example.com/pic.jpg",
        }
        with patch(
            "apps.users.views.google_id_token.verify_oauth2_token",
            return_value=fake_info,
        ):
            resp = api_client.post(
                self.URL, {"id_token": "valid-token"}, format="json"
            )
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["email"] == email

        # User + Profile rows should be created
        user = User.objects.get(email=email)
        assert user.is_allowlisted
        assert Profile.objects.filter(user=user).exists()

    def test_upserts_existing_user(self, api_client, participant):
        new_picture = "https://example.com/new-pic.jpg"
        fake_info = {
            "sub": "google-789",
            "email": participant.email,
            "given_name": "Updated",
            "family_name": "Name",
            "picture": new_picture,
        }
        with patch(
            "apps.users.views.google_id_token.verify_oauth2_token",
            return_value=fake_info,
        ):
            resp = api_client.post(
                self.URL, {"id_token": "valid-token"}, format="json"
            )
        assert resp.status_code == 200
        participant.refresh_from_db()
        assert participant.avatar_url == new_picture


@pytest.mark.django_db
class TestMeView:
    URL = "/api/auth/me/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 401

    def test_returns_current_user(self, auth_client, participant):
        resp = auth_client.get(self.URL)
        assert resp.status_code == 200
        assert resp.data["email"] == participant.email


@pytest.mark.django_db
class TestProfileView:
    URL = "/api/auth/profile/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 401

    def test_get_profile(self, auth_client, participant):
        resp = auth_client.get(self.URL)
        assert resp.status_code == 200
        assert "consent_symptom_logging" in resp.data

    def test_patch_profile(self, auth_client, participant):
        resp = auth_client.patch(
            self.URL,
            {"consent_symptom_logging": True, "consent_ai_context": True},
            format="json",
        )
        assert resp.status_code == 200
        participant.profile.refresh_from_db()
        assert participant.profile.consent_symptom_logging is True
        assert participant.profile.consent_ai_context is True
