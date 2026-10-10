"""
Tests for health-log endpoints:
  GET/POST /api/health/meals/
  GET/DEL  /api/health/meals/<pk>/
  GET/POST /api/health/symptoms/
  GET/POST /api/health/water/
  GET/POST /api/health/weight/
  GET      /api/health/admin/summary/  (admin only)
"""
import pytest
from unittest.mock import patch
from django.utils import timezone

from apps.health.models import MealLog, SymptomLog, WaterLog, WeightLog


@pytest.mark.django_db
class TestMealLog:
    LIST_URL = "/api/health/meals/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.LIST_URL)
        assert resp.status_code == 401

    def test_list_empty(self, auth_client):
        resp = auth_client.get(self.LIST_URL)
        assert resp.status_code == 200
        assert resp.data["count"] == 0

    def test_create_meal_calls_edamam(self, auth_client, participant):
        edamam_resp = {
            "calories": 350,
            "totalNutrients": {
                "PROCNT": {"quantity": 12.0},
                "CHOCDF": {"quantity": 45.0},
                "FAT": {"quantity": 10.0},
                "FIBTG": {"quantity": 3.0},
            },
        }
        with patch("apps.health.views.http_requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.return_value = edamam_resp
            resp = auth_client.post(
                self.LIST_URL,
                {"food_query": "oatmeal with berries", "timestamp": timezone.now().isoformat()},
                format="json",
            )
        assert resp.status_code == 201
        assert resp.data["food_query"] == "oatmeal with berries"
        assert resp.data["calories"] == 350

    def test_create_meal_handles_edamam_timeout(self, auth_client, participant):
        import requests as req_lib
        with patch(
            "apps.health.views.http_requests.post",
            side_effect=req_lib.exceptions.Timeout,
        ):
            resp = auth_client.post(
                self.LIST_URL,
                {"food_query": "unknown food", "timestamp": timezone.now().isoformat()},
                format="json",
            )
        # Should still create the log — just without nutrition data
        assert resp.status_code == 201
        assert resp.data["calories"] is None

    def test_user_cannot_see_other_users_meals(self, auth_client, make_user, participant):
        other = make_user(email="other@example.com")
        MealLog.objects.create(
            user=other,
            timestamp=timezone.now(),
            food_query="secret salad",
        )
        resp = auth_client.get(self.LIST_URL)
        assert resp.data["count"] == 0

    def test_delete_own_meal(self, auth_client, participant):
        meal = MealLog.objects.create(
            user=participant,
            timestamp=timezone.now(),
            food_query="toast",
        )
        resp = auth_client.delete(f"/api/health/meals/{meal.pk}/")
        assert resp.status_code == 204
        assert not MealLog.objects.filter(pk=meal.pk).exists()

    def test_cannot_delete_other_users_meal(self, auth_client, make_user):
        other = make_user(email="other2@example.com")
        meal = MealLog.objects.create(
            user=other,
            timestamp=timezone.now(),
            food_query="their lunch",
        )
        resp = auth_client.delete(f"/api/health/meals/{meal.pk}/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestSymptomLog:
    LIST_URL = "/api/health/symptoms/"

    def test_blocked_without_consent(self, auth_client, participant):
        participant.profile.consent_symptom_logging = False
        participant.profile.save()
        resp = auth_client.post(
            self.LIST_URL,
            {"symptom": "headache", "severity": 1, "timestamp": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == 403

    def test_create_with_consent(self, auth_client, participant):
        participant.profile.consent_symptom_logging = True
        participant.profile.save()
        resp = auth_client.post(
            self.LIST_URL,
            {"symptom": "fatigue", "severity": 2, "timestamp": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["symptom"] == "fatigue"


@pytest.mark.django_db
class TestWaterLog:
    URL = "/api/health/water/"

    def test_create_and_list(self, auth_client, participant):
        resp = auth_client.post(
            self.URL,
            {"amount_ml": 250, "timestamp": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == 201
        list_resp = auth_client.get(self.URL)
        assert list_resp.data["count"] == 1


@pytest.mark.django_db
class TestWeightLog:
    URL = "/api/health/weight/"

    def test_create_and_list(self, auth_client, participant):
        resp = auth_client.post(
            self.URL,
            {"weight_kg": "65.5", "timestamp": timezone.now().isoformat()},
            format="json",
        )
        assert resp.status_code == 201
        list_resp = auth_client.get(self.URL)
        assert list_resp.data["count"] == 1


@pytest.mark.django_db
class TestAdminHealthSummary:
    URL = "/api/health/admin/summary/"

    def test_blocked_for_participant(self, auth_client):
        resp = auth_client.get(self.URL)
        assert resp.status_code == 403

    def test_accessible_for_admin(self, admin_client):
        resp = admin_client.get(self.URL)
        assert resp.status_code == 200
        assert "total_meal_logs" in resp.data
