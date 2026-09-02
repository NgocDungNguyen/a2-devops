"""
Integration tests — failure modes and misconfiguration.

The assignment brief asks for this by name, separately from the happy-path
suites: "Also test the basic failure modes: broken connections between
frontend, backend and database, and misconfiguration that only shows up in
a deployed environment (wrong API URL, wrong ALLOWED_HOSTS, missing static
files...)." This file is that requirement.

Two things distinguish it from test_health_smoke.py: that file proves the
probes answer correctly when everything is healthy; this one proves they
answer correctly — with the *right* status code, not a 500 or a hang — when
something underneath them is actually broken. A liveness/readiness probe
that itself crashes when the database is down is worse than useless during
an incident, which is exactly the scenario every test below simulates.
"""

from unittest.mock import patch

import pytest
from django.db import connections
from django.db.utils import OperationalError
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

pytestmark = pytest.mark.integration


class DatabaseFailureTests(APITestCase):
    """README: '/readyz/ ... checks the database and storage and returns
    503 when either is down.' Simulated here without an actual dead
    database, so the test is deterministic and needs no real Postgres."""

    def test_readyz_reports_503_when_the_database_is_unreachable(self):
        with patch.object(
            connections["default"], "cursor", side_effect=OperationalError("simulated outage")
        ):
            response = self.client.get("/readyz/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["database"], "unavailable")

    def test_readyz_still_reports_storage_even_when_the_database_is_down(self):
        # Both dependencies are checked independently — a database outage
        # must not short-circuit the storage check and hide a second
        # problem behind the first one's stack trace.
        with patch.object(
            connections["default"], "cursor", side_effect=OperationalError("simulated outage")
        ):
            response = self.client.get("/readyz/")

        self.assertIn("storage", response.data)
        self.assertEqual(response.data["storage"], "ok")

    def test_healthz_stays_up_even_when_the_database_is_completely_down(self):
        # The whole reason healthz and readyz are two different endpoints:
        # README again — "A liveness probe that checks the database will
        # restart a perfectly healthy application server because the
        # database was briefly slow." Prove healthz genuinely does not care.
        with patch.object(
            connections["default"], "cursor", side_effect=OperationalError("simulated outage")
        ):
            response = self.client.get("/healthz/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})


class StorageFailureTests(APITestCase):
    def test_readyz_reports_503_when_storage_is_unreachable(self):
        with patch("apps.core.views.default_storage") as mock_storage:
            mock_storage.exists.side_effect = OSError("simulated storage outage")
            response = self.client.get("/readyz/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["storage"], "unavailable")
        # Database was never touched by the mock, so it must still read ok —
        # same independence guarantee as the database-down case above.
        self.assertEqual(response.data["database"], "ok")


class AllowedHostsMisconfigurationTests(APITestCase):
    """README's Troubleshooting section, converted into a regression test:

    'A load balancer health check arrives with a Host header of the
    instance's private IP. If that is not in ALLOWED_HOSTS, Django answers
    400 and the target group marks a perfectly healthy instance unhealthy.'

    This is the single most-cited deployment gotcha in the whole README —
    worth pinning down so a future settings change can't silently
    reintroduce it.
    """

    @override_settings(ALLOWED_HOSTS=["store.example.com"])
    def test_a_request_with_an_unrecognised_host_header_is_rejected_with_400(self):
        response = self.client.get("/healthz/", HTTP_HOST="169.254.169.254")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(ALLOWED_HOSTS=["store.example.com"])
    def test_the_configured_host_is_still_accepted(self):
        # Proves the test above is failing for the right reason — a
        # restrictive ALLOWED_HOSTS still lets its own host through, so the
        # 400 above is specifically about the *unrecognised* header, not a
        # broken test fixture.
        response = self.client.get("/healthz/", HTTP_HOST="store.example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(ALLOWED_HOSTS=["store.example.com"])
    def test_an_unrecognised_host_is_rejected_on_an_api_route_too(self):
        # Not just the probes — the same failure must be visible (and
        # correctly coded) on the routes the SPA actually calls.
        response = self.client.get("/api/products/", HTTP_HOST="169.254.169.254")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
