#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def settings_module_from_env_file():
    """Read DJANGO_SETTINGS_MODULE out of .env, if it is set there.

    This has to happen here rather than in config/settings/base.py. Django
    reads DJANGO_SETTINGS_MODULE to decide *which* settings module to import,
    so by the time base.py calls read_env() the choice has already been made -
    which meant setting this variable in .env silently did nothing, and
    `manage.py migrate` on a production box quietly ran with dev settings.

    A real environment variable still wins: this only fills in the blank.
    """
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return None
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("DJANGO_SETTINGS_MODULE") and "=" in line:
            value = line.split("=", 1)[1].strip().strip("'\"")
            if value:
                return value
    return None


def main():
    # Precedence: the shell environment, then .env, then development - which
    # is the safe default so a freshly cloned checkout runs without exporting
    # anything first.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        settings_module_from_env_file() or "config.settings.dev",
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available "
            "on your PYTHONPATH environment variable? Did you forget to "
            "activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
