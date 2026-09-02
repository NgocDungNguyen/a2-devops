# Testing strategy

This repository shipped with **no test suite at all** — the README says so
explicitly, and writing one is part of the assignment. This document covers
what was built, why each kind of test was chosen, and the exact commands
Role 2 wires into the Jenkinsfile's `test` and post-deploy `smoke` stages.

Everything here is designed around one constraint from the brief: **the
CI/CD pipeline cannot function without a passing test stage.** A failing
suite has to fail the build with a non-zero exit code and a report Jenkins
can publish — every command below does both.

## The four (really six) suites

| # | Kind                                          | Location                                                        | What it proves                                                                                                                                                                                                                                                                                                                         | Runs against                                   |
| - | --------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 1 | **Unit** — payment gateway             | `server/apps/orders/tests/test_payments_unit.py`              | Every documented test card (approve/decline), Luhn validation, brand detection, expiry and CVC rules — all in isolation, no DB                                                                                                                                                                                                        | Pure Python functions                          |
| 2 | **Unit** — tax & cart totals           | `server/apps/orders/tests/test_pricing_unit.py`               | `money()` rounding and `tax_for()` reproduce the README's worked example ($44.95 + $27.95 → $72.90 subtotal, $2.25 tax, $75.15 total) to the cent                                                                                                                                                                                 | Pure Python functions                          |
| 3 | **Integration** — checkout             | `server/apps/orders/tests/test_checkout_integration.py`       | Placing an order decrements stock exactly once; a declined card creates no order and takes no stock; cancelling restocks; a member can't set fulfilment status                                                                                                                                                                         | Real HTTP → real DB (SQLite in test settings) |
| 4 | **Integration** — catalogue            | `server/apps/catalog/tests/test_catalog_integration.py`       | `GET /api/products/` actually returns seeded rows (API↔DB connectivity); inactive products/brands never appear, on the list *or* the detail route; filtering, ordering and search work                                                                                                                                            | Real HTTP → real DB                           |
| 5 | **Integration** — authorisation matrix | `server/apps/core/tests/test_authorization_matrix.py`         | Every role (anonymous / member / merchant / admin) gets the*exact* status code it should from every major endpoint; a deactivated merchant loses access without losing the role; scoped querysets 404 rather than leak                                                                                                               | Real HTTP → real DB                           |
| 6 | **Smoke** — in-process                 | `server/apps/core/tests/test_health_smoke.py`                 | `/healthz/`, `/readyz/`, `/api/version/`, `/api/config/` behave correctly, fast, as part of the normal test run                                                                                                                                                                                                                | Django test client                             |
| 7 | **Smoke** — live deployment            | `scripts/smoke_test.py`                                       | The*actual deployed* instance answers over real HTTP — the check a post-deploy pipeline stage or an ELB target group runs                                                                                                                                                                                                           | A running instance, any environment            |
| 8 | **Web UI / E2E**                        | `e2e/tests/*.spec.js` (Playwright) — 7 files, 11 tests       | Six of the README's acceptance journeys, converted to browser tests exactly as the README invites ("each one converts into an end-to-end test") — see the breakdown below (Journey B alone spans two files: the approved-card path and the declined-card path)                                                                                                                                                             | Frontend + backend + DB, all real              |
| 9 | **Integration** — failure modes        | `server/apps/core/tests/test_misconfiguration_integration.py` | The brief's explicit "test the basic failure modes" line:`/readyz/` reports 503 with the right per-dependency detail when the database or storage is actually down, `/healthz/` stays up regardless, and an unrecognised `Host` header — the README's most-cited deployment gotcha — is rejected with 400 rather than crashing | Real HTTP, DB/storage failures simulated       |

That's 4 distinct *kinds* (unit, integration, E2E, smoke) across 9 files,
covering the areas the brief calls out by name: payment logic, server-side
tax/total math, the stock decrement, a full browser journey, and the
misconfiguration/failure-mode scenarios that only show up in a deployed
environment.

### The E2E suite, journey by journey

The README's "Verifying a deployment" section lists six acceptance journeys,
lettered A–F, and says outright that they are "a ready-made backlog" for
E2E tests. All six are now covered:

| Journey | README name                          | Spec file                                                                                                                                                                                                                                                                                   |
| ------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A       | Anonymous browsing                   | `smoke.spec.js` (catalogue rendering, filtering is covered by the backend's `test_catalog_integration.py`; the browser-specific slice — the SPA actually renders what the API returns — is what this file checks)                                                                     |
| B       | Register and buy                     | `purchase-journey.spec.js`, `declined-payment.spec.js`                                                                                                                                                                                                                                  |
| C       | Fulfilment                           | `order-fulfilment.spec.js`                                                                                                                                                                                                                                                                |
| D       | Reviews and wishlist                 | `reviews-and-wishlist.spec.js`                                                                                                                                                                                                                                                            |
| E       | The seller lifecycle ("the big one") | `seller-lifecycle.spec.js` — the only spec that crosses three roles (public applicant, administrator, seller) through one continuous piece of state, and the only one that depends on a real outgoing email reaching its destination. **Needs one extra setup step** — see below. |
| F       | Administration                       | `admin-catalog-management.spec.js`                                                                                                                                                                                                                                                        |

### Running Journey E (the seller lifecycle) — one extra step

Every other spec works against the backend exactly as Plan A leaves it. This
one doesn't, for a specific reason: accepting a merchant invitation needs the
signup link the API emails out, and the default (console) email backend
prints that link to whichever terminal is attached to `manage.py runserver`'s
stdout — readable by a human, unreachable by a separate Node/Playwright
process.

The fix costs nothing in application code, because email delivery in this
project is already "pluggable... purely through environment variables" (the
README's own words). Start the backend with the file-based backend instead
of the default:

```bash
cd server
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend \
EMAIL_FILE_PATH="$(pwd)/.dev-emails" \
python manage.py runserver 0.0.0.0:8000
```

Then point the test at the same directory:

```bash
cd e2e
E2E_EMAIL_DIR="$(pwd)/../server/.dev-emails" npx playwright test tests/seller-lifecycle.spec.js
```

If `E2E_EMAIL_DIR` is not set, this one spec calls `test.skip()` with a
message pointing back here — it does not fail the build, so a pipeline stage
that hasn't been wired up for Journey E yet won't block on it by accident.
`server/.dev-emails/` is gitignored; nothing here needs to be committed.

One line in `server/config/settings/base.py` was added to make this
possible: `EMAIL_FILE_PATH = env("EMAIL_FILE_PATH", default=...)`, sitting
right next to the other `EMAIL_*` settings. Without it, `EMAIL_FILE_PATH` in
the environment was simply never read into Django's settings — django-environ
only wires through variables a settings module explicitly asks for — so the
file-based backend would fail (silently: see `apps/core/emails.py`'s
"failures are logged, never raised" policy) every time. This is the only
application-code change made while building this test suite; everything else
in this document is test code.

## Why these, and not something else

- **Unit tests target the two places a silent bug costs real money**: the
  payment gateway (which decides whether a customer is charged) and the tax
  arithmetic (which decides how much). Both are pure functions with zero
  external dependencies, so they run in milliseconds and can't be flaky —
  exactly what you want gating every commit.
- **Integration tests target the one place money and inventory move
  together** (checkout) and the property the whole authorisation model rests
  on (deny by default, scoped to role and owner). A manual click-through of
  the demo store won't reliably catch a stock double-decrement or a
  forgotten permission class; a table-driven test across four roles will.
- **E2E tests are reserved for what only a real browser can prove**: that
  the frontend actually calls the backend, that a Vue router guard and a
  Django permission agree with each other, and that a shopper — not a test
  client — sees the right toast when a card is declined. Organised one spec
  file per acceptance journey rather than one per page, because the value
  here is the *journey* connecting every tier, not exhaustive UI coverage
  (that's what component tests would be for, and this app has none of those
  yet — a reasonable next investment, noted in Known Bugs/Problems).
- **Two smoke suites, not one**, because they answer different questions at
  different pipeline stages. The in-process version runs in the `test` stage
  in milliseconds, before an image is even built. The live script runs
  *after* a deploy, against the thing that was actually deployed — the only
  way to catch a `DisallowedHost`, a missing `DATABASE_URL`, or a container
  that built fine but never actually started serving traffic.

## Running everything locally

### Backend (unit + integration + in-process smoke)

```bash
cd server
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                  # pulls in requirements.txt too

pytest                       # every suite, plain console output
pytest -m unit                # suites #1-2 only
pytest -m integration          # suites #3-5 only
pytest -m smoke                # suite #6 only
```

Every test is a plain `django.test.TestCase` / `rest_framework.test.APITestCase`
underneath `pytest-django`'s collection, so `python manage.py test` also
works with **zero extra dependencies** — useful on a bare agent that only
has `requirements.txt` installed, or as a fallback if `pytest` itself is
unavailable:

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test apps
```

### Live smoke test (suite #7)

```bash
python3 scripts/smoke_test.py --base-url http://localhost:8000
python3 scripts/smoke_test.py --base-url https://staging.example.com --retries 5 --retry-delay 5
python3 scripts/smoke_test.py --base-url https://prod.example.com --expect-commit "$(git rev-parse HEAD)"
```

No install step — it's the Python standard library only.

### End-to-end (suite #8)

Requires both dev servers running first (see the README's Plan A, Steps 6–7),
or point `E2E_BASE_URL` at any deployed environment:

```bash
cd e2e
npm install
npx playwright install --with-deps chromium   # once, downloads the browser

npx playwright test                            # against http://localhost:5173
E2E_BASE_URL=https://staging.example.com npx playwright test
```

`seller-lifecycle.spec.js` additionally needs `E2E_EMAIL_DIR` (and the
backend started with the file-based email backend) — see "Running Journey E"
above; every other spec runs against the default setup with nothing extra.

**A note on parallelism.** Playwright defaults to running several browsers
at once locally. Against `manage.py runserver` — a development server, not
what actually serves staging or production — six or more of these
journeys hammering it simultaneously can make an otherwise-correct test time
out under load rather than fail for a real reason. If a local run is flaky,
narrow it:

```bash
npx playwright test --workers=2
```

This is specifically a `runserver` limitation, not a limitation of the
tests or the application: gunicorn (what Plan B, the Dockerfile and every
later plan actually run) handles concurrent requests properly with multiple
worker processes, so a CI/staging environment built the way the README
describes shouldn't need `--workers` throttled at all. Confirmed by running
every spec individually (all pass) and the full suite at `--workers=2`
(all pass) — the only failures seen while building this suite were at full
default parallelism (8 workers on this machine) against the single-threaded
dev server, and they were different tests on different runs, which is the
signature of contention rather than a bug in a specific spec.

**A note on rate limits — read this before wiring the E2E stage into CI.**
`config/settings/base.py`'s `DEFAULT_THROTTLE_RATES` (`THROTTLE_AUTH=20/min`,
`THROTTLE_MERCHANT_APPLY=5/hour` by default — see `server/.env.example`)
are tuned to stop a *person* abusing the login or seller-application forms.
They are not tuned for a test suite that logs in over a dozen times and
submits at least one seller application every single run. Confirmed by
direct reproduction, not guesswork:

```bash
# 25 rapid logins against a freshly-restarted server:
# the first 20 succeed (200), the rest come back 429 - an exact match for
# THROTTLE_AUTH=20/min, reproduced directly rather than assumed.
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code} " -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@rmit.edu.au","password":"RmitStore2767!"}'
done
```

Run this suite enough times within an hour — which a real pipeline does
naturally, commit after commit — and both throttles will eventually trip
and fail unrelated specs with what looks like a broken login or a broken
`/sell` form, when the app is actually working exactly as designed. Two
ways to handle it in the pipeline, no application code changes needed
either way since both rates are already environment-driven:

1. **Give the staging environment its own, higher rate** via the same env
   vars the README already documents:
   `THROTTLE_AUTH=200/min THROTTLE_MERCHANT_APPLY=200/hour` (or similar) on
   the staging deploy only — production keeps the tight defaults.
2. **Accept the default rate and space pipeline runs out accordingly** —
   viable if commits are infrequent enough that the E2E stage naturally
   runs less than ~15-20 times an hour.

Option 1 is what this session used to get a clean, repeatable local
verification run; it is the more realistic choice for an actively-developed
pipeline.

## Exact commands for the Jenkinsfile

These are the commands Role 2 should call from pipeline stages — copy-paste
ready. Every one produces a report Jenkins can publish and exits non-zero on
failure, which is what makes "if an update fails during testing... production
must not be updated" (Core Requirement 4) enforceable.

```groovy
stage('Backend: install & test') {
    steps {
        dir('server') {
            sh 'python3 -m venv .venv'
            sh '.venv/bin/pip install -r requirements-dev.txt'
            sh '''
                .venv/bin/pytest \
                    --junitxml=results/junit.xml \
                    --cov=apps --cov-report=xml:results/coverage.xml --cov-report=term
            '''
        }
    }
    post {
        always {
            junit 'server/results/junit.xml'
            // Cobertura / Coverage plugin reads results/coverage.xml
        }
    }
}

stage('Frontend: install & build') {
    steps {
        dir('client') {
            sh 'npm ci'
            sh 'npm run build'   // produces client/dist/, the deployable artifact
        }
    }
}

stage('E2E: web UI journeys') {
    // Runs against the just-built frontend + a running backend — typically
    // after `docker compose up -d` in a CI-only compose file, or against
    // the same staging environment the next stage is about to promote from.
    //
    // EMAIL_FILE_PATH here is what makes seller-lifecycle.spec.js runnable
    // in the pipeline: the staging deploy step should start the API with
    // EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend and
    // this same path, so E2E_EMAIL_DIR below can read the merchant
    // invitation link straight off disk. Every other spec ignores it.
    //
    // The staging deploy step should also start the API with a raised
    // THROTTLE_AUTH / THROTTLE_MERCHANT_APPLY (see "A note on rate limits"
    // above) — otherwise this stage will start failing unrelated specs with
    // spurious login/apply failures once it has run ~15-20 times in an hour,
    // which a busy day of commits will do easily.
    environment {
        E2E_BASE_URL = "${STAGING_URL}"
        E2E_EMAIL_DIR = "${STAGING_EMAIL_DIR}"
    }
    steps {
        dir('e2e') {
            sh 'npm ci'
            sh 'npx playwright install --with-deps chromium'
            sh 'npx playwright test'   // all 7 spec files, 11 tests
        }
    }
    post {
        always {
            junit 'e2e/results/junit.xml'
            publishHTML(target: [
                reportDir: 'e2e/results/html', reportFiles: 'index.html',
                reportName: 'Playwright report', keepAll: true
            ])
        }
    }
}

stage('Deploy to staging') {
    steps {
        // ... Ansible / docker deploy steps ...
    }
}

stage('Smoke test staging') {
    steps {
        sh "python3 scripts/smoke_test.py --base-url ${STAGING_URL} --retries 5 --retry-delay 5"
    }
    // A non-zero exit here fails the stage automatically — wire the
    // pipeline's post{failure{}} block to email the team (Core Requirement 8)
    // and stop before the "Deploy to production" stage ever runs.
}

stage('Deploy to production') {
    when { expression { currentBuild.resultIsBetterOrEqualTo('SUCCESS') } }
    steps {
        // ... promote the same artifact built above; see the README's note
        // on why the frontend bundle never needs rebuilding per environment ...
    }
}

stage('Smoke test production') {
    steps {
        sh "python3 scripts/smoke_test.py --base-url ${PROD_URL} --expect-commit ${GIT_COMMIT} --retries 5 --retry-delay 5"
    }
}
```

Report files a Jenkins job should archive/publish, all generated by the
commands above:

- `server/results/junit.xml` — JUnit plugin
- `server/results/coverage.xml` — Cobertura/Coverage plugin
- `e2e/results/junit.xml` — JUnit plugin (same step, aggregates with the backend's)
- `e2e/results/html/` — HTML Publisher plugin (Playwright's trace/screenshot report, invaluable when a UI test fails on a headless agent)

## Known gaps and how to close them (for the report's "Known Bugs/Problems" section)

- ~~`apps/orders/views.py:OrderViewSet.get_queryset()` annotated and paginated
  `Order` without an explicit `.order_by()` on the list branch, so Django
  emitted an `UnorderedObjectListWarning` under pagination.~~ **Fixed.**
  `Sum("items__quantity")` forces a `GROUP BY`, which is what made Django
  lose track of whether `Order.Meta.ordering` still applied — the fix adds
  `.order_by("-created_at")` explicitly right after the `.annotate()` call.
  Confirmed by re-running the full suite: the warning is gone and all 102
  backend tests still pass.
- ~~E2E specs that needed "any product" grabbed a bare
  `.product-card().first()` on the shop grid. Two real, evidenced bugs fell
  out of that once the suite had been run enough times: (1) it could land
  on a transient product another spec had already deleted mid-run, and
  (2) seeded stock is never replenished, so whichever product sorts first
  eventually runs out from real repeated purchases — confirmed directly:
  after this session's own repeated verification, "Campus Threads Graphic
  Hoodie - Black" hit `quantity: 0` for real.~~ **Fixed.** `helpers.js`'s
  `realCatalogueCards()` now filters out both "E2E"-named cards and any
  card showing the "Out of stock" badge, so the suite stays correct as
  real stock depletes over the pipeline's lifetime rather than needing a
  re-fix every time the current first product sells out.
- ~~`admin-catalog-management.spec.js` assumed a row it had just created
  would be on page 1 of its dashboard list. True only while that list
  stays under 20 items (`LargePagination`'s page size) — and
  `seller-lifecycle.spec.js` creates one brand per run that, matching the
  README's actual journey, is never deleted, so the *brand* list alone
  grows by one every time that spec runs (categories are unaffected —
  nothing in this suite creates a category without also deleting it in
  the same run). Confirmed directly, twice: brands went from the 16 seeded
  to 27 over the course of this session's own repeated verification
  (queried via `/api/manage/brands/`), comfortably past the 20-item page
  size, and the row genuinely was there — just on page 2, not page 1.~~
  **Fixed.** `helpers.js`'s new `findRowAcrossPages()`
  pages forward through `PaginationBar.vue` until it finds the row (or
  confirms it truly isn't there), used everywhere this spec looks up
  something it just created. The first version of this helper had its own
  bug — an instant `.count()` check that could run before the list's own
  async fetch had resolved, indistinguishable from "not on this page" —
  fixed to actively poll (`waitFor({state: 'visible', timeout: 2000})`) on
  each page before moving on.
- **No component-level frontend tests.** `PaymentForm`'s digit-grouping
  (`groupDigits()`), `CartDrawer`'s quantity clamping
  (`maxPurchaseQuantity()`), and the cart store's line-merging logic are
  exercised only indirectly, through the browser, in the E2E suite. To close
  this:

  1. `cd client && npm install -D vitest @vue/test-utils jsdom`
  2. Add a `test` script to `client/package.json` and a minimal
     `vitest.config.js` (environment: `jsdom`).
  3. Write `client/src/components/store/__tests__/PaymentForm.spec.js`
     mounting the component directly and asserting `groupDigits()`'s output
     for a 16-digit Visa vs. a 15-digit Amex, and that `complete` flips to
     `true` only once every field is valid — the exact three cases the E2E
     suite currently only proves indirectly by clicking the "use a test
     number" buttons.
  4. This becomes a genuine fifth *kind* of test (component, not E2E) for
     the report, and it runs in milliseconds compared to a browser spin-up —
     worth having in CI even with the E2E suite in place, the same argument
     used above for keeping backend unit tests separate from integration
     tests.
- **E2E runs Chromium only.** Cross-browser coverage is a one-line change —
  add `{ name: 'firefox', use: { ...devices['Desktop Firefox'] } }` and the
  WebKit equivalent to the `projects` array in `e2e/playwright.config.js` —
  deliberately left for later because tripling browser downloads and run
  time in every pipeline execution is a real cost for a teaching app with a
  20-minute demo video limit. If it's worth doing before submission, do it
  as a **separate, manually-triggered Jenkins stage** (not on every commit)
  so the fast default pipeline stays fast — a good "additional enhancement"
  to mention in the report either way.
