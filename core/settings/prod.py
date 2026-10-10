"""
Production settings — strict security, HTTPS enforced, env-var driven.
"""
from .base import *  # noqa: F401, F403

DEBUG = False

# Render provides the service hostname at runtime. Keep explicit hosts for
# custom domains while allowing the default *.onrender.com hostname.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")
RENDER_HOSTS = {
    "pmos-backend-ss6g.onrender.com",
    RENDER_EXTERNAL_HOSTNAME,
}
ALLOWED_HOSTS = [
    *ALLOWED_HOSTS,
    *(host for host in RENDER_HOSTS if host and host not in ALLOWED_HOSTS),
]

# ── HTTPS / security headers ──────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# ── Logging ───────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
