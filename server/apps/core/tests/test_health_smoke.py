"""
Smoke tests — the health/readiness/version probes, run in-process.

These are the fast half of the smoke-test story described in the assignment
brief: "GET /healthz/ and GET /readyz/ return healthy, and GET /api/version/
reports the build you just deployed... the cheapest and most valuable tests
in the whole pipeline." This file runs them in-process against Django's test
client as part of the normal `pytest` / `manage.py test` run, so a broken
probe fails the CI "test" stage in seconds, before a single container is
built.

That is deliberately not the same job as scripts/smoke_test.py at the
repository root, which pings a *running, deployed* instance's real HTTP
port over the network — the one thing an in-process test can never verify is
that the process actually starts, binds a port, and answers a request from
outside its own test runner. Use this file in the "test" stage; use
scripts/smoke_test.py as the "post-deploy" gate against staging and
production. See that script's docstring for the full pipeline placement.
"""

import pytest
from django.db import connections
from rest_framework import status
from rest_framework.test import APITestCase

pytestmark = pytest.mark.smoke


class HealthzTests(APITestCase):
    def test_healthz_is_public_and_returns_ok(self):
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok"})

    def test_healthz_requires_no_authentication(self):
        # No force_authenticate() anywhere in this test - if this endpoint
        # ever grows an auth requirement, an ELB health check silently starts
        # failing with no error a human would see.
        response = self.client.get("/healthz/")
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_healthz_does_not_touch_the_database(self):
        # A liveness probe that queries the database will restart a healthy
        # process because the database was briefly slow. Prove it by closing
        # every connection first: if healthz still answers, it never opened
        # a new one.
        for conn in connections.all():
            conn.close()
        response = self.client.get("/healthz/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReadyzTests(APITestCase):
    def test_readyz_reports_database_and_storage_ok(self):
        response = self.client.get("/readyz/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"database": "ok", "storage": "ok"})

    def test_readyz_requires_no_authentication(self):
        response = self.client.get("/readyz/")
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VersionTests(APITestCase):
    def test_version_endpoint_reports_configured_build_metadata(self):
        from django.test import override_settings

        with override_settings(APP_VERSION="9.9.9", GIT_COMMIT="deadbeef"):
            response = self.client.get("/api/version/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["version"], "9.9.9")
        self.assertEqual(response.data["commit"], "deadbeef")


class PublicConfigTests(APITestCase):
    def test_config_endpoint_reports_the_configured_tax_rate(self):
        response = self.client.get("/api/config/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("sales_tax_rate", response.data)
        self.assertIn("currency", response.data)
