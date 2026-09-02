#!/usr/bin/env python3
# RMIT University Vietnam
# Course: COSC2767 | COSC2805 Systems Deployment and Operations
# Assessment: Assignment 2 — CI/CD Pipeline
#
# Deployment smoke test — pings a *running, deployed* instance over real
# HTTP, exactly the way an ELB target group health check or a human with
# curl would. This is the live-deployment half of the smoke-test story the
# assignment brief calls "the cheapest and most valuable tests in the whole
# pipeline"; see server/apps/core/tests/test_health_smoke.py for the
# in-process half that runs during the "test" stage, before anything is
# deployed at all.
#
# Deliberately dependency-free (standard library only: urllib, json,
# argparse). A smoke test that itself needs `pip install requests` before it
# can tell you whether the deploy worked is a smoke test with a chicken-and
# -egg problem on a fresh Jenkins agent or a minimal container image. This
# script runs with nothing but a system Python 3.
#
# Pipeline placement (see ../TESTING.md for the full command reference):
#   Run this AFTER a deploy, BEFORE routing real traffic to it — the classic
#   use is the first health check after `docker compose up` / a systemd
#   restart / a new task lands behind the load balancer:
#
#     python3 scripts/smoke_test.py --base-url http://<staging-host>
#     python3 scripts/smoke_test.py --base-url http://<prod-host> --expect-commit "$GIT_COMMIT"
#
# Exit code is 0 only if every check passes — wire it straight into the
# pipeline as a gate: a non-zero exit fails the Jenkins stage, which (per
# the assignment's Continuous Deployment requirement) must stop production
# from being updated and notify the team.
"""Ping a deployed RMIT Store instance and report whether it is healthy."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _get(url: str, timeout: float) -> tuple[int, dict | None, str]:
    """GET a URL and return (status_code, parsed_json_or_None, raw_text).

    Never raises for a non-2xx response — a 503 from /readyz/ is data this
    script needs to read, not an exception to unwind. Only a connection
    failure (DNS, refused, timeout) is allowed to propagate, and the caller
    turns that into a failed CheckResult instead of a stack trace.
    """
    request = urllib.request.Request(url, headers={"User-Agent": "rmit-store-smoke-test"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status_code = response.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status_code = exc.code

    try:
        parsed = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = None
    return status_code, parsed, raw


def check_healthz(base_url: str, timeout: float) -> CheckResult:
    url = f"{base_url}/healthz/"
    try:
        status_code, body, raw = _get(url, timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return CheckResult("GET /healthz/ (liveness)", False, f"unreachable: {exc}")

    if status_code != 200:
        return CheckResult("GET /healthz/ (liveness)", False, f"HTTP {status_code}: {raw[:200]}")
    if not body or body.get("status") != "ok":
        return CheckResult("GET /healthz/ (liveness)", False, f"unexpected body: {raw[:200]}")
    return CheckResult("GET /healthz/ (liveness)", True, "200 {\"status\": \"ok\"}")


def check_readyz(base_url: str, timeout: float) -> CheckResult:
    url = f"{base_url}/readyz/"
    try:
        status_code, body, raw = _get(url, timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return CheckResult("GET /readyz/ (readiness)", False, f"unreachable: {exc}")

    if status_code == 503:
        return CheckResult(
            "GET /readyz/ (readiness)",
            False,
            f"503 - a dependency is down: {raw[:200]}",
        )
    if status_code != 200:
        return CheckResult("GET /readyz/ (readiness)", False, f"HTTP {status_code}: {raw[:200]}")
    if not body or body.get("database") != "ok" or body.get("storage") != "ok":
        return CheckResult("GET /readyz/ (readiness)", False, f"unexpected body: {raw[:200]}")
    return CheckResult("GET /readyz/ (readiness)", True, "200 database=ok storage=ok")


def check_version(
    base_url: str,
    timeout: float,
    expect_commit: str | None,
    expect_version: str | None,
) -> CheckResult:
    url = f"{base_url}/api/version/"
    try:
        status_code, body, raw = _get(url, timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return CheckResult("GET /api/version/ (build id)", False, f"unreachable: {exc}")

    if status_code != 200 or not body or "version" not in body or "commit" not in body:
        return CheckResult("GET /api/version/ (build id)", False, f"HTTP {status_code}: {raw[:200]}")

    detail = f"version={body['version']} commit={body['commit']}"

    if expect_version and body["version"] != expect_version:
        return CheckResult(
            "GET /api/version/ (build id)",
            False,
            f"{detail} - expected version {expect_version}. "
            "Docker Swarm may still be serving a previous replica.",
        )

    if expect_commit and body["commit"] != expect_commit:
        return CheckResult(
            "GET /api/version/ (build id)",
            False,
            f"{detail} - expected commit {expect_commit}. "
            "The load balancer may still be serving the previous build.",
        )
    return CheckResult("GET /api/version/ (build id)", True, detail)


def check_catalog_reachable(base_url: str, timeout: float) -> CheckResult:
    """The one check that proves the whole chain, not just the API process.

    /healthz/ and /readyz/ touch nothing and the database respectively, but
    neither confirms that a real API request reaches the database *and*
    that the response makes it back through whatever reverse proxy or load
    balancer sits in front (see the README's ALLOWED_HOSTS / DisallowedHost
    troubleshooting entry — a misconfigured Host header fails exactly here,
    not at /healthz/).
    """
    url = f"{base_url}/api/products/"
    try:
        status_code, body, raw = _get(url, timeout)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return CheckResult("GET /api/products/ (API -> DB round trip)", False, f"unreachable: {exc}")

    if status_code != 200 or not body or "results" not in body:
        return CheckResult(
            "GET /api/products/ (API -> DB round trip)", False, f"HTTP {status_code}: {raw[:200]}"
        )
    return CheckResult(
        "GET /api/products/ (API -> DB round trip)",
        True,
        f"200, {body.get('count', '?')} products in the catalogue",
    )


CHECKS = [check_healthz, check_readyz, check_catalog_reachable]


def check_version_samples(
    base_url: str,
    timeout: float,
    expect_commit: str | None,
    expect_version: str | None,
    samples: int,
) -> CheckResult:
    last_detail = ""

    for sample in range(1, samples + 1):
        result = check_version(
            base_url,
            timeout,
            expect_commit,
            expect_version,
        )

        if not result.ok:
            return CheckResult(
                result.name,
                False,
                f"sample {sample}/{samples}: {result.detail}",
            )

        last_detail = result.detail

        if sample < samples:
            time.sleep(0.2)

    return CheckResult(
        "GET /api/version/ (build id)",
        True,
        f"{samples}/{samples} samples matched; {last_detail}",
    )


def run(
    base_url: str,
    timeout: float,
    retries: int,
    retry_delay: float,
    expect_commit: str | None,
    expect_version: str | None,
    version_samples: int,
):
    base_url = base_url.rstrip("/")
    attempt = 0

    while True:
        attempt += 1
        results = [check(base_url, timeout) for check in CHECKS]
        results.append(
            check_version_samples(
                base_url,
                timeout,
                expect_commit,
                expect_version,
                version_samples,
            )
        )

        if all(result.ok for result in results) or attempt > retries:
            return results

        time.sleep(retry_delay)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Origin of the deployed API, e.g. http://localhost:8000 or "
        "https://staging.rmit-store.example (default: %(default)s)",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-request timeout, seconds")
    parser.add_argument(
        "--retries",
        type=int,
        default=0,
        help="Extra attempts if any check fails, waiting --retry-delay between them. "
        "Useful right after a deploy while the new container is still starting.",
    )
    parser.add_argument("--retry-delay", type=float, default=3.0, help="Seconds between retries")
    parser.add_argument(
        "--expect-commit",
        default=None,
        help="If set, fail unless GET /api/version/ reports this exact GIT_COMMIT.",
    )
    parser.add_argument(
        "--expect-version",
        default=None,
        help="If set, fail unless GET /api/version/ reports this exact APP_VERSION.",
    )
    parser.add_argument(
        "--version-samples",
        type=int,
        default=1,
        help="Number of consecutive version responses that must match (default: 1).",
    )
    args = parser.parse_args()

    if args.version_samples < 1:
        parser.error("--version-samples must be at least 1")

    print(f"Smoke testing {args.base_url} ...")
    results = run(
        args.base_url,
        args.timeout,
        args.retries,
        args.retry_delay,
        args.expect_commit,
        args.expect_version,
        args.version_samples,
    )

    failures = 0
    for result in results:
        icon = "PASS" if result.ok else "FAIL"
        print(f"  [{icon}] {result.name} - {result.detail}")
        if not result.ok:
            failures += 1

    if failures:
        print(f"\n{failures} of {len(results)} checks failed. Instance is NOT healthy.")
        return 1

    print(f"\nAll {len(results)} checks passed. Instance is healthy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
