"""
Create or update an administrator without an interactive prompt.

    python manage.py create_admin --email you@rmit.edu.au --password 'Secret123!'

or, reading from the environment (which is what a container entrypoint or an
Ansible task wants):

    DJANGO_SUPERUSER_EMAIL=you@rmit.edu.au \
    DJANGO_SUPERUSER_PASSWORD='Secret123!' \
    python manage.py create_admin

Idempotent: running it against an existing account updates the password and
makes sure the roles are right, rather than failing.
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = "Create or update a store administrator, non-interactively."

    def add_arguments(self, parser):
        parser.add_argument("--email", default=os.environ.get("DJANGO_SUPERUSER_EMAIL"))
        parser.add_argument(
            "--password", default=os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        )
        parser.add_argument("--first-name", default="Store")
        parser.add_argument("--last-name", default="Admin")

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]

        if not email or not password:
            raise CommandError(
                "An email and a password are required. Pass --email and "
                "--password, or set DJANGO_SUPERUSER_EMAIL and "
                "DJANGO_SUPERUSER_PASSWORD."
            )

        user, created = User.objects.get_or_create(
            email=email.lower(),
            defaults={
                "first_name": options["first_name"],
                "last_name": options["last_name"],
            },
        )
        user.role = Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        verb = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} administrator {user.email}"))
