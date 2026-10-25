"""
Admin access: a single account configured through settings, HTTP Basic on every request (stateless).

Public: browse products, place an order. Admin: write products, list orders. Anything else is denied.
"""
import base64
import binascii
import logging
import secrets
import threading
from hmac import compare_digest

from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

log = logging.getLogger(__name__)

_lock = threading.Lock()
_generated_password: str | None = None


def admin_credentials() -> tuple[str, str]:
    """(username, password). Generates and logs a random password once if none is configured."""
    global _generated_password
    user = settings.SHOP_ADMIN_USER
    password = settings.SHOP_ADMIN_PASSWORD
    if password:
        return user, password
    with _lock:
        if _generated_password is None:
            _generated_password = secrets.token_urlsafe(24)
            log.warning(
                "SHOP_ADMIN_PASSWORD is not set. Generated admin credentials for this run: %s / %s",
                user, _generated_password,
            )
        return user, _generated_password


class AdminPrincipal:
    """What request.user is after a successful login. There are no Django users involved."""
    is_authenticated = True
    is_anonymous = False
    is_admin = True

    def __init__(self, username: str):
        self.username = username
        self.pk = username

    def __str__(self):
        return self.username


class AdminBasicAuthentication(BaseAuthentication):
    # No authenticate_header(): the 401 carries no WWW-Authenticate, so browsers never show a login dialog
    # or cache credentials. API clients send the Authorization header themselves.

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != b"basic":
            return None  # anonymous; endpoints decide whether that is allowed
        if len(parts) != 2:
            raise AuthenticationFailed()
        try:
            decoded = base64.b64decode(parts[1], validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            raise AuthenticationFailed()
        given_user, _, given_password = decoded.partition(":")

        user, password = admin_credentials()
        # Evaluate both comparisons (constant time) so timing doesn't reveal which half was wrong.
        user_ok = compare_digest(given_user.encode(), user.encode())
        password_ok = compare_digest(given_password.encode(), password.encode())
        if not (user_ok and password_ok):
            raise AuthenticationFailed()
        return (AdminPrincipal(user), None)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(getattr(request.user, "is_admin", False))
