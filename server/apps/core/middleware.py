"""Visitor-activity tracking for the monitoring dashboard.

A single middleware that notes "this visitor was seen just now" in the
database, so /metrics/activity/ can answer how many distinct people used the
store in the last few minutes. See ActiveVisitor's docstring for why this is
a table and not a cache.

Two properties matter more than the counting itself:

* It must never break a request. Every failure path is swallowed — a store
  that stopped selling because its own monitoring hit a database hiccup
  would be monitoring done backwards.
* It must not turn every request into a write. Each worker remembers which
  visitors it has written recently and only touches the database once per
  visitor per minute.
"""

import hashlib
import logging
import time

from django.utils import timezone

logger = logging.getLogger("apps.core.health")

# Machine traffic, not people: probes, the metrics scraper itself, and asset
# paths that nginx normally serves anyway.
_EXCLUDED_PREFIXES = (
    "/healthz",
    "/readyz",
    "/metrics",
    "/static",
    "/media",
    "/favicon",
)

# At most one database write per visitor per interval, per worker process.
_WRITE_INTERVAL_SECONDS = 60

# visitor_hash -> time.monotonic() of this process's last write for it.
_recent_writes = {}


class VisitorActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            self._record(request)
        except Exception:  # noqa: BLE001 — metrics must never fail a request
            logger.debug("visitor activity not recorded", exc_info=True)
        return response

    def _record(self, request):
        if request.path.startswith(_EXCLUDED_PREFIXES):
            return

        visitor = self._visitor_key(request)
        if visitor is None:
            return

        now = time.monotonic()
        last_write = _recent_writes.get(visitor)
        if last_write is not None and now - last_write < _WRITE_INTERVAL_SECONDS:
            return

        # Crude bound so a scan of the store from many addresses cannot grow
        # this dict forever. Clearing merely costs a few extra UPSERTs.
        if len(_recent_writes) > 10_000:
            _recent_writes.clear()
        _recent_writes[visitor] = now

        from apps.core.models import ActiveVisitor

        try:
            ActiveVisitor.objects.update_or_create(
                visitor_hash=visitor, defaults={"last_seen": timezone.now()}
            )
        except Exception:  # noqa: BLE001 — e.g. database briefly unavailable
            _recent_writes.pop(visitor, None)
            logger.debug("visitor activity write skipped", exc_info=True)

    @staticmethod
    def _visitor_key(request):
        """A stable, anonymous identity for whoever sent this request.

        JWT authentication happens inside DRF's view layer, after middleware
        has already run, so request.user is useless here — and it would miss
        anonymous shoppers anyway. IP (first hop of X-Forwarded-For, set by
        the frontend nginx) plus user agent, hashed, identifies a "person"
        well enough for a dashboard without storing anything personal.
        """
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        if not ip:
            return None
        agent = request.META.get("HTTP_USER_AGENT", "")[:200]
        return hashlib.sha256(f"{ip}|{agent}".encode()).hexdigest()
