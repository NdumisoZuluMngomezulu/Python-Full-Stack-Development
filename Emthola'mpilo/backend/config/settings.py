"""
Settings for the Hearth & Co. shop API.

Everything environment-specific is read from environment variables (see README).
The defaults are for local development only.
"""
import os
from pathlib import Path

from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str) -> list[str]:
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


# --- Core -------------------------------------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", "1")  # set DJANGO_DEBUG=0 in production

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DJANGO_DEBUG is off.")
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",  # DRF needs AnonymousUser; no Django users or sessions are used
    "corsheaders",
    "rest_framework",
    "shop.apps.ShopConfig",
]

# No sessions, cookies or CSRF middleware: the API is stateless (admin uses HTTP Basic on every request).
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must come first so it answers preflight before anything else
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

# --- Database ---------------------------------------------------------------------------------------------------
# SQLite by default so the project runs with zero setup. Set DB_ENGINE=mysql to use MySQL 8 like the original.
# (Unlike Spring's createDatabaseIfNotExist, Django will not create the database for you: CREATE DATABASE shop.)
if os.environ.get("DB_ENGINE", "sqlite").lower() == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "shop"),
            "USER": os.environ.get("DB_USER", "root"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
            # IMMEDIATE takes the write lock when a transaction starts, so concurrent orders queue up instead of
            # failing with "database is locked" halfway through (Django 5.1+).
            "OPTIONS": {"transaction_mode": "IMMEDIATE", "timeout": 20},
        }
    }

# --- REST framework ---------------------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["shop.auth.AdminBasicAuthentication"],
    # Deny by default; public endpoints opt in with AllowAny.
    "DEFAULT_PERMISSION_CLASSES": ["shop.auth.IsAdmin"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": None,
    "EXCEPTION_HANDLER": "shop.errors.api_exception_handler",
    # Prices go out as JSON numbers (18.0), not strings, exactly like the Spring API.
    "COERCE_DECIMAL_TO_STRING": False,
}

# --- CORS -------------------------------------------------------------------------------------------------------
# Not needed in development when you use the Vite proxy (same origin), but required if the React build is served
# from a different origin than the API.
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
)
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_HEADERS = [*default_headers, "idempotency-key"]
CORS_EXPOSE_HEADERS = ["Idempotent-Replayed"]

# --- Shop -------------------------------------------------------------------------------------------------------
# Admin account for product writes and order listing (HTTP Basic).
# If SHOP_ADMIN_PASSWORD is empty, a random password is generated and logged once per process at startup.
# That fallback is for local development only: with several server processes each one would invent its own.
SHOP_ADMIN_USER = os.environ.get("SHOP_ADMIN_USER", "admin")
SHOP_ADMIN_PASSWORD = os.environ.get("SHOP_ADMIN_PASSWORD", "")
