"""
Tests for campaign endpoints:
  GET /api/campaigns/
  GET /api/campaigns/<pk>/
"""
import pytest
from django.utils import timezone
from datetime import timedelta

from apps.campaigns.models import Campaign


@pytest.fixture
def active_campaign(db):
    return Campaign.objects.create(
        title="Summer Wellness",
        description="Stay active this summer.",
        start_date=timezone.now().date(),
        end_date=(timezone.now() + timedelta(days=30)).date(),
        status=Campaign.Status.ACTIVE,
    )


@pytest.fixture
def inactive_campaign(db):
    return Campaign.objects.create(
        title="Old Campaign",
        description="Archived.",
        start_date=(timezone.now() - timedelta(days=60)).date(),
        end_date=(timezone.now() - timedelta(days=30)).date(),
        status=Campaign.Status.COMPLETED,
    )


@pytest.mark.django_db
class TestCampaignList:
    URL = "/api/campaigns/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 401

    def test_lists_all_campaigns(self, auth_client, active_campaign, inactive_campaign):
        resp = auth_client.get(self.URL)
        assert resp.status_code == 200
        assert resp.data["count"] == 2

    def test_filter_by_status(self, auth_client, active_campaign, inactive_campaign):
        resp = auth_client.get(self.URL + "?status=active")
        assert resp.status_code == 200
        assert resp.status_code < 500


@pytest.mark.django_db
class TestCampaignDetail:
    def test_retrieve_campaign(self, auth_client, active_campaign):
        resp = auth_client.get(f"/api/campaigns/{active_campaign.pk}/")
        assert resp.status_code == 200
        assert resp.data["title"] == "Summer Wellness"
        assert resp.data["status"] == Campaign.Status.ACTIVE

    def test_returns_404_for_unknown(self, auth_client):
        resp = auth_client.get("/api/campaigns/99999/")
        assert resp.status_code == 404
