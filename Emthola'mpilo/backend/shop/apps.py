import os
import sys

from django.apps import AppConfig


def _is_serving() -> bool:
    """True in a process that will answer HTTP requests (not migrate, test, shell, ...)."""
    argv = sys.argv
    if len(argv) > 1 and os.path.basename(argv[0]) == "manage.py":
        # runserver's autoreloader starts a child with RUN_MAIN=true; that is the one that serves.
        return argv[1] == "runserver" and (os.environ.get("RUN_MAIN") == "true" or "--noreload" in argv)
    return True  # gunicorn, uwsgi, daphne, ...


class ShopConfig(AppConfig):
    name = "shop"

    def ready(self):
        if _is_serving():
            # Resolve the admin credentials now so a generated password is printed at startup, not on first use.
            from .auth import admin_credentials
            admin_credentials()
