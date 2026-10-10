from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import GoogleAuthView, MeView, ProfileView

urlpatterns = [
    path("google/", GoogleAuthView.as_view(), name="auth-google"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
    path("profile/", ProfileView.as_view(), name="auth-profile"),
]
