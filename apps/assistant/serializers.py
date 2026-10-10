"""
Serializers for the assistant app.
"""
from rest_framework import serializers
from .models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "updated_at", "messages"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChatMessageCreateSerializer(serializers.Serializer):
    """Payload sent by the frontend when the user sends a message."""
    session_id = serializers.IntegerField(required=False, allow_null=True)
    message = serializers.CharField(max_length=4000)
