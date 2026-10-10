"""
Development settings — DEBUG on, SQLite for local dev, relaxed security.
"""
from .base import *  # noqa: F401, F403

DEBUG = True

# Allow Django dev server
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Accept requests from the Next.js dev server
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ── SQLite for local dev — no Postgres required ───────────────
# Override the DATABASE_URL-based config from base.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Use console email backend in dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

