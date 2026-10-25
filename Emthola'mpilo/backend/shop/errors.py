"""Uniform JSON errors: every failure is {"error": "<message>"}, like the original Spring API."""
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ApiError(APIException):
    """Raise anywhere (including inside a transaction, which then rolls back) to return `status_code` + message."""

    def __init__(self, status_code: int, message: str):
        super().__init__(detail=message)
        self.status_code = status_code


def api_exception_handler(exc, context):
    # DRF turns "not authenticated" into 403 when the authenticator has no WWW-Authenticate challenge.
    # We deliberately send none (so browsers never pop up a login dialog), but still want a 401.
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return Response({"error": "Authentication required."}, status=401)
    if isinstance(exc, PermissionDenied):
        return Response({"error": "Forbidden."}, status=403)
    if isinstance(exc, ValidationError):
        # Same message as the original; `fields` is extra detail a form can use.
        return Response({"error": "Check your details and try again.", "fields": exc.detail}, status=400)

    response = drf_exception_handler(exc, context)
    if response is not None:
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        response.data = {"error": str(detail) if detail else "Request failed."}
    return response
