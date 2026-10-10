from django.urls import path

from .views import ChatMessageView, ChatSessionDetailView, ChatSessionListCreateView

urlpatterns = [
    path("sessions/", ChatSessionListCreateView.as_view(), name="chat-session-list"),
    path("sessions/<int:pk>/", ChatSessionDetailView.as_view(), name="chat-session-detail"),
    path("chat/", ChatMessageView.as_view(), name="chat-message"),
]
