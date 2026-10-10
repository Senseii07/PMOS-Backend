"""
Views for the AI assistant — chat sessions and message endpoint.
"""
import logging

from django.conf import settings
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.health.models import AuditLog, MealLog, SymptomLog

from .models import ChatMessage, ChatSession
from .serializers import ChatMessageCreateSerializer, ChatSessionSerializer

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a supportive health campaign assistant for the Serene Wellness app. "
    "Your role is to provide general wellness guidance, nutritional information, "
    "and motivational support to campaign participants.\n\n"
    "RULES YOU MUST ALWAYS FOLLOW:\n"
    "1. Always include a disclaimer that responses are for informational purposes "
    "only and NOT a substitute for professional medical advice, diagnosis, or treatment.\n"
    "2. Never provide a definitive medical diagnosis.\n"
    "3. If a user describes symptoms that could indicate a medical emergency "
    "(chest pain, difficulty breathing, severe pain, signs of stroke), immediately "
    "direct them to call emergency services (911 or local equivalent).\n"
    "4. For concerning but non-emergency symptoms, always recommend consulting a "
    "qualified healthcare professional.\n"
    "5. Be warm, supportive, and non-judgmental in all responses.\n"
)


def _build_context_block(user) -> str:
    """Return a brief health context string if the user has consented to AI context."""
    profile = getattr(user, "profile", None)
    if not profile or not profile.consent_ai_context:
        return ""
    lines = ["[User health context — treat as private]\n"]
    for m in MealLog.objects.filter(user=user).order_by("-timestamp")[:5]:
        lines.append(
            f"  Meal: {m.food_query} ({m.calories} kcal, {m.timestamp:%Y-%m-%d})"
        )
    for s in SymptomLog.objects.filter(user=user).order_by("-timestamp")[:5]:
        lines.append(
            f"  Symptom: {s.symptom} severity {s.severity}/3 {s.timestamp:%Y-%m-%d}"
        )
    return "\n".join(lines)


def _call_ai(messages: list) -> str:
    """Dispatch to OpenAI or Anthropic based on settings.AI_PROVIDER."""
    provider = getattr(settings, "AI_PROVIDER", "openai")
    model = getattr(settings, "AI_MODEL", "gpt-4o")

    if provider == "openai":
        from openai import OpenAI  # noqa: PLC0415
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=model, messages=messages, max_tokens=1024, temperature=0.7
        )
        return resp.choices[0].message.content

    if provider == "anthropic":
        import anthropic  # noqa: PLC0415
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        non_system = [m for m in messages if m["role"] != "system"]
        resp = client.messages.create(
            model=model, max_tokens=1024, system=system, messages=non_system
        )
        return resp.content[0].text

    raise ValueError(f"Unknown AI_PROVIDER: {provider!r}")


class ChatSessionListCreateView(generics.ListCreateAPIView):
    """GET /api/assistant/sessions/  — list sessions for the current user.
    POST — create a new empty session (title optional).
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            ChatSession.objects.filter(user=self.request.user)
            .prefetch_related("messages")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatSessionDetailView(generics.RetrieveDestroyAPIView):
    """GET /api/assistant/sessions/<pk>/  — retrieve with full message history.
    DELETE — destroy the session and all its messages.
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            ChatSession.objects.filter(user=self.request.user)
            .prefetch_related("messages")
        )


class ChatMessageView(APIView):
    """
    POST /api/assistant/chat/
    Body:  { "session_id": <int|null>, "message": "<string>" }
    Returns: { session_id, user_message, assistant_message }

    If session_id is omitted a new session is created automatically.
    User health logs are injected into the system prompt when the profile
    has consent_ai_context == True.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data.get("session_id")
        user_text = serializer.validated_data["message"]
        user = request.user

        # Resolve or create the session
        if session_id:
            try:
                session = ChatSession.objects.get(pk=session_id, user=user)
            except ChatSession.DoesNotExist:
                return Response(
                    {"detail": "Session not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            session = ChatSession.objects.create(user=user)

        # Build message list for the AI
        history = list(
            session.messages.order_by("created_at").values("role", "content")
        )
        context_block = _build_context_block(user)
        system_content = (
            SYSTEM_PROMPT + f"\n\n{context_block}" if context_block else SYSTEM_PROMPT
        )
        ai_messages = [{"role": "system", "content": system_content}]
        ai_messages += [{"role": m["role"], "content": m["content"]} for m in history]
        ai_messages.append({"role": "user", "content": user_text})

        # Persist the user message and write an audit entry
        user_msg = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=user_text
        )
        try:
            AuditLog.objects.create(
                actor=user,
                target_user=user,
                action=AuditLog.Action.CREATE,
                resource_type="ChatMessage",
                resource_id=user_msg.pk,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Audit log write failed: %s", exc)

        # Call the AI provider
        try:
            ai_text = _call_ai(ai_messages)
        except Exception as exc:  # noqa: BLE001
            logger.error("AI call failed: %s", exc)
            return Response(
                {
                    "detail": (
                        "The AI assistant is temporarily unavailable. "
                        "Please try again later."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Persist the assistant reply and touch the session timestamp
        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.ASSISTANT, content=ai_text
        )
        session.save(update_fields=["updated_at"])

        return Response(
            {
                "session_id": session.pk,
                "user_message": {"role": "user", "content": user_text},
                "assistant_message": {"role": "assistant", "content": ai_text},
            },
            status=status.HTTP_200_OK,
        )

