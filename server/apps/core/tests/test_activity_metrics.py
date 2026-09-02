"""
The visitor-activity pipeline behind the monitoring dashboard.

Three moving parts, three things to prove:

* VisitorActivityMiddleware records a row per distinct visitor — and does NOT
  record machine traffic (probes, the metrics endpoint itself).
* /metrics/activity/ counts those rows per time window, without auth, because
  the CloudWatch publisher that scrapes it has no JWT.
* A database failure while recording must not fail the shopper's request —
  monitoring that can take the store down is monitoring pointed backwards.
"""

from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core import middleware
from apps.core.models import ActiveVisitor

pytestmark = pytest.mark.integration


class VisitorActivityMiddlewareTests(APITestCase):
    def setUp(self):
        # The middleware's per-process write throttle outlives the test
        # database rollback; start each test with a clean slate.
        middleware._recent_writes.clear()

    def test_public_request_records_one_visitor(self):
        self.client.get("/api/config/", HTTP_USER_AGENT="test-browser")
        self.assertEqual(ActiveVisitor.objects.count(), 1)

    def test_repeat_requests_from_one_visitor_stay_one_row(self):
        for _ in range(3):
            self.client.get("/api/config/", HTTP_USER_AGENT="test-browser")
        self.assertEqual(ActiveVisitor.objects.count(), 1)

    def test_distinct_visitors_record_distinct_rows(self):
        self.client.get("/api/config/", HTTP_USER_AGENT="browser-one")
        self.client.get("/api/config/", HTTP_USER_AGENT="browser-two")
        self.assertEqual(ActiveVisitor.objects.count(), 2)

    def test_forwarded_for_header_identifies_the_real_client(self):
        # Through the frontend nginx every request's REMOTE_ADDR is the proxy;
        # X-Forwarded-For is what distinguishes actual people.
        self.client.get(
            "/api/config/",
            HTTP_USER_AGENT="same-browser",
            HTTP_X_FORWARDED_FOR="203.0.113.10",
        )
        self.client.get(
            "/api/config/",
            HTTP_USER_AGENT="same-browser",
            HTTP_X_FORWARDED_FOR="203.0.113.20",
        )
        self.assertEqual(ActiveVisitor.objects.count(), 2)

    def test_probe_and_metrics_traffic_is_not_counted(self):
        self.client.get("/healthz/")
        self.client.get("/readyz/")
        self.client.get("/metrics/activity/")
        self.assertEqual(ActiveVisitor.objects.count(), 0)

    def test_a_recording_failure_never_fails_the_request(self):
        with mock.patch(
            "apps.core.models.ActiveVisitor.objects.update_or_create",
            side_effect=Exception("database on fire"),
        ):
            response = self.client.get("/api/config/", HTTP_USER_AGENT="x")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ActivityMetricsEndpointTests(APITestCase):
    def test_requires_no_authentication(self):
        response = self.client.get("/metrics/activity/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_counts_visitors_per_window(self):
        now = timezone.now()
        ActiveVisitor.objects.create(visitor_hash="a" * 64, last_seen=now)
        ActiveVisitor.objects.create(
            visitor_hash="b" * 64, last_seen=now - timedelta(minutes=3)
        )
        ActiveVisitor.objects.create(
            visitor_hash="c" * 64, last_seen=now - timedelta(minutes=10)
        )

        response = self.client.get("/metrics/activity/")

        self.assertEqual(response.data["active_visitors_1m"], 1)
        self.assertEqual(response.data["active_visitors_5m"], 2)
        self.assertEqual(response.data["active_visitors_15m"], 3)

    def test_prunes_rows_older_than_a_day(self):
        ActiveVisitor.objects.create(
            visitor_hash="d" * 64,
            last_seen=timezone.now() - timedelta(hours=25),
        )
        self.client.get("/metrics/activity/")
        self.assertFalse(
            ActiveVisitor.objects.filter(visitor_hash="d" * 64).exists()
        )
