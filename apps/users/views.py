"""
Views for authentication and user profile management.
"""
import logging

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AllowListEntry, Profile, User
from .permissions import IsOwnerOrAdmin
from .serializers import GoogleAuthSerializer, ProfileSerializer, UserSerializer

logger = logging.getLogger(__name__)


def _get_tokens_for_user(user: User) -> dict:
    """Return a pair of JWT access + refresh tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class GoogleAuthView(APIView):
    """
    POST /api/auth/google/

    Accepts the Google ID token issued by the frontend (NextAuth),
    verifies it server-side against Google's public keys, checks the
    allow-list, upserts the User record, and returns a JWT pair.
    """

    permission_classes = [AllowAny]
    serializer_class = GoogleAuthSerializer

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        raw_token = serializer.validated_data["id_token"]

        # ── 1. Verify the token against Google's public keys ──────────
        try:
            id_info = google_id_token.verify_oauth2_token(
                raw_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            logger.warning("Invalid Google ID token: %s", exc)
            return Response(
                {"detail": "Invalid Google ID token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = id_info.get("email", "").lower().strip()
        google_id = id_info.get("sub")

        if not email or not google_id:
            return Response(
                {"detail": "Token missing required claims."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ── 2. Check the allow-list ────────────────────────────────────
        if not AllowListEntry.objects.filter(email=email).exists():
            return Response(
                {"detail": "not_invited"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── 3. Upsert the user ────────────────────────────────────────
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "google_id": google_id,
                "first_name": id_info.get("given_name", ""),
                "last_name": id_info.get("family_name", ""),
                "avatar_url": id_info.get("picture", ""),
                "is_allowlisted": True,
            },
        )

        if not created:
            # Keep google_id and avatar in sync
            updated_fields = []
            if user.google_id != google_id:
                user.google_id = google_id
                updated_fields.append("google_id")
            new_avatar = id_info.get("picture", "")
            if new_avatar and user.avatar_url != new_avatar:
                user.avatar_url = new_avatar
                updated_fields.append("avatar_url")
            if not user.is_allowlisted:
                user.is_allowlisted = True
                updated_fields.append("is_allowlisted")
            if updated_fields:
                user.save(update_fields=updated_fields)

        # Create a Profile row if one doesn't exist yet
        Profile.objects.get_or_create(user=user)

        # ── 4. Issue JWT ───────────────────────────────────────────────
        tokens = _get_tokens_for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                **tokens,
            },
            status=status.HTTP_200_OK,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/   — return the current user + profile
    PATCH /api/auth/me/  — update first_name / last_name
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/auth/profile/  — return the current user's profile
    PATCH /api/auth/profile/  — update profile fields
    """

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile
