"""
Tests for the AI assistant endpoints:
  GET/POST  /api/assistant/sessions/
  GET/DEL   /api/assistant/sessions/<pk>/
  POST      /api/assistant/chat/
"""
import pytest
from unittest.mock import patch

from apps.assistant.models import ChatMessage, ChatSession


@pytest.mark.django_db
class TestChatSessionListCreate:
    URL = "/api/assistant/sessions/"

    def test_requires_auth(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == 401

    def test_list_own_sessions_only(self, auth_client, make_user, participant):
        other = make_user(email="other@example.com")
        ChatSession.objects.create(user=participant, title="mine")
        ChatSession.objects.create(user=other, title="theirs")
        resp = auth_client.get(self.URL)
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["title"] == "mine"

    def test_create_session(self, auth_client):
        resp = auth_client.post(self.URL, {"title": "New session"}, format="json")
        assert resp.status_code == 201
        assert resp.data["title"] == "New session"


@pytest.mark.django_db
class TestChatSessionDetail:
    def test_retrieve_own_session(self, auth_client, participant):
        session = ChatSession.objects.create(user=participant, title="my session")
        resp = auth_client.get(f"/api/assistant/sessions/{session.pk}/")
        assert resp.status_code == 200
        assert resp.data["title"] == "my session"

    def test_cannot_retrieve_other_users_session(self, auth_client, make_user):
        other = make_user(email="other3@example.com")
        session = ChatSession.objects.create(user=other, title="private")
        resp = auth_client.get(f"/api/assistant/sessions/{session.pk}/")
        assert resp.status_code == 404

    def test_delete_own_session(self, auth_client, participant):
        session = ChatSession.objects.create(user=participant)
        resp = auth_client.delete(f"/api/assistant/sessions/{session.pk}/")
        assert resp.status_code == 204
        assert not ChatSession.objects.filter(pk=session.pk).exists()


@pytest.mark.django_db
class TestChatMessageView:
    URL = "/api/assistant/chat/"

    def test_requires_auth(self, api_client):
        resp = api_client.post(self.URL, {"message": "hello"}, format="json")
        assert resp.status_code == 401

    def test_requires_message_field(self, auth_client):
        resp = auth_client.post(self.URL, {}, format="json")
        assert resp.status_code == 400

    def test_creates_new_session_when_none_provided(self, auth_client, participant):
        with patch("apps.assistant.views._call_ai", return_value="Hello! How can I help?"):
            resp = auth_client.post(
                self.URL, {"message": "Hi there"}, format="json"
            )
        assert resp.status_code == 200
        assert "session_id" in resp.data
        assert resp.data["assistant_message"]["content"] == "Hello! How can I help?"
        # Verify messages persisted
        session = ChatSession.objects.get(pk=resp.data["session_id"])
        assert session.user == participant
        assert session.messages.count() == 2

    def test_continues_existing_session(self, auth_client, participant):
        session = ChatSession.objects.create(user=participant)
        with patch("apps.assistant.views._call_ai", return_value="Here is some info."):
            resp = auth_client.post(
                self.URL,
                {"message": "Tell me more", "session_id": session.pk},
                format="json",
            )
        assert resp.status_code == 200
        assert resp.data["session_id"] == session.pk

    def test_returns_404_for_unknown_session(self, auth_client):
        resp = auth_client.post(
            self.URL, {"message": "Hi", "session_id": 99999}, format="json"
        )
        assert resp.status_code == 404

    def test_handles_ai_provider_error_gracefully(self, auth_client):
        with patch(
            "apps.assistant.views._call_ai",
            side_effect=RuntimeError("OpenAI down"),
        ):
            resp = auth_client.post(
                self.URL, {"message": "Hello"}, format="json"
            )
        assert resp.status_code == 503
        assert "unavailable" in resp.data["detail"].lower()

    def test_context_block_excluded_without_consent(self, auth_client, participant):
        participant.profile.consent_ai_context = False
        participant.profile.save()
        captured = {}
        def fake_ai(messages):
            captured["messages"] = messages
            return "OK"
        with patch("apps.assistant.views._call_ai", side_effect=fake_ai):
            auth_client.post(self.URL, {"message": "hi"}, format="json")
        system_msg = captured["messages"][0]["content"]
        assert "[User health context" not in system_msg
