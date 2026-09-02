<p align="center">
    <img src="https://i.imgur.com/Om7ww0e.png" width=900>
</p>

# RMIT Store 🛒 - Django + Vue edition

The RMIT Store sells glorious and wholesome RMIT merchandise: lanyards, hoodies,
T-shirts, cups and more. It exists to enrich student life on campus by offering
official university apparel that fosters identity, inclusivity and connection.

This is the **COSC2767 Systems Deployment and Operations** teaching application.
The store itself is a means to an end - your job is to get it running on AWS and
to keep it running well.

---

## 🔬 What is this stack?

Three tiers, three separate concerns, three things you can deploy independently:

- **Vue 3** - the frontend single-page application, built with Vite.
- **Django 5 + Django REST Framework** - the backend REST API.
- **PostgreSQL** - the relational database.
- **Gunicorn** - the WSGI server that runs Django in anything that is not
  development.

Supporting pieces you will meet along the way:

- **SimpleJWT** for token authentication (access + refresh tokens)
- **Pinia** for frontend state management
- **django-storages** for optional S3 media storage

## 🏪 Features

A complete three-role storefront: shoppers browse and buy, sellers list
products under their own brand, administrators run the place. Everything
listed below is implemented - there are no stubbed screens.

### 🛍️ Storefront - no account required

A home page with a featured row; a catalogue at `/shop` with per-category and
per-brand landing pages, filtering by category, brand, price range and minimum
rating, and six sort orders taken from a server-side whitelist; name search with
a navbar autosuggest; paginated product pages carrying photography, live stock,
the star breakdown and approved reviews; a brands directory; a contact form and
newsletter signup, both throttled; and the public *become a seller* form.
Inactive products, brands and categories never appear on the storefront,
whatever URL is guessed.

**The home page.** A promotional carousel and the *Top rated* row, both fed
from the seeded catalogue.

![RMIT Store home page showing the Holiday specials carousel and the Top rated product row](screenshots/homepage.png)

**The catalogue at `/shop`.** Filters down the left, 12 of 47 products per
page. This one screen proves the whole chain is connected: the browser reached
the SPA, the SPA reached the API, and the API reached the database.

![The shop page with price, rating and category filters beside a grid of product cards](screenshots/shop-catalogue.png)

**A product page.** Photography, live stock, the price and the star summary.

![A product page showing the image, price, stock level and star rating](screenshots/product-page.png)

Scroll down and the approved reviews and the star breakdown are underneath.

![The review list and rating breakdown on a product page](screenshots/product-reviews.png)

### 👤 For members (shoppers)

Register, sign in, edit a profile, change or reset a password, and manage
delivery addresses. Sessions use JWT access and refresh tokens: they survive a
reload, refresh silently in the background, and signing out blacklists the
refresh token server-side rather than just clearing the browser. The shopping
bag is held in the browser, persists across reloads, stays in step between tabs,
and caps quantities against live stock.

Checkout computes prices, tax and the total **on the server** from the product
rows - the client sends only ids, quantities and the card. Members then get
order history with per-line fulfilment status, line-item cancellation that
returns stock, product reviews and a wishlist. Line items snapshot the product's
name, image and price, so history stays correct after a product is renamed,
repriced or withdrawn.

**Registering**, which is where journey B starts.

![The registration form with name, email and password fields](screenshots/register.png)

**Signing in.** A successful sign-in stores an access and a refresh token in
the browser, which is why the session survives a reload.

![The sign-in page with email and password fields](screenshots/login.png)

**The bag.** Held in the browser, so it survives a reload and stays in step
between tabs. The card form is underneath the running subtotal.

![The bag drawer with two products, quantity steppers and a subtotal of $72.90](screenshots/cart-drawer.png)

**The account dashboard.** Profile, security, addresses, orders and wishlist
down the left.

![The member account dashboard showing account details and the sidebar menu](screenshots/account-dashboard.png)

**Order history**, and an order opened up. Note the arithmetic is worth
checking by hand - 5% tax applies to the taxable line only.

![The order history list showing one placed order](screenshots/order-history.png)

![An order detail page showing subtotal $72.90, sales tax $2.25, total $75.15, Visa ending 4242 and a Paid badge](screenshots/order-detail.png)

**The wishlist**, filled by the heart on any product card.

![The wishlist panel in the account dashboard](screenshots/wishlist.png)

### 🧑‍🍳 For sellers (merchants)

Apply through the public form. An administrator approves, which provisions the
account - an existing shopper is promoted in place, a new seller gets a signed,
self-expiring invitation link to choose a password - and creates their brand.
Sellers then manage their own products, including image upload, and their own
brand. Every seller queryset is narrowed to them, so somebody else's product id
returns `404` rather than `403`, and the endpoint cannot be used to probe for
which ids exist. Deactivating a seller cascades to their brand and all of its
products.

**The public application form** at `/sell`.

![The become a seller application form](screenshots/seller-application.png)

**A seller's product list.** Two things to notice, because both are the
authorisation model showing through the interface: the menu is shorter than an
administrator's - no Users, Categories, Sellers or Reviews - and the list holds
only the five Campus Threads products belonging to this seller, out of 47 in
the store.

![The seller dashboard listing only the five Campus Threads products, with a shorter sidebar menu](screenshots/merchant-products.png)

### 🛠️ For administrators

Full CRUD over products, categories and brands; seller applications and
accounts; a review moderation queue where rejecting a review removes it from
the product page *and* from the average; the user list; and every order in the
store, with line items movable along the fulfilment path. A product attached to
a historical order cannot be deleted - the API says so and suggests
deactivating it instead. Django's own admin at `/admin/` is there too, which is
the quickest way to inspect a deployment without going through the SPA.

**Catalogue management.** The full 47 products, with stock and status.

![The administrator product list with stock levels, status badges and edit and delete actions](screenshots/admin-products.png)

**Every order in the store**, with each line item movable along the fulfilment
path.

![The administrator order list showing orders across all customers](screenshots/admin-orders.png)

**The review moderation queue.** Rejecting a review removes it from the product
page *and* from the average.

![The review moderation queue with approve and reject controls](screenshots/admin-review-moderation.png)

**Seller applications and accounts**, where an application is approved and the
invitation is sent.

![The seller management screen listing applications and their approval status](screenshots/admin-sellers.png)

### 🔐 Security and correctness

The things a marker is likely to poke at, all enforced by the API rather than
by the interface:

- **Deny by default** - DRF is configured so that every endpoint requires
  authentication unless it explicitly opts out. Forgetting a permission class
  fails closed.
- **Three roles** - `admin`, `merchant`, `member`, held on the user record and
  distinct from Django's `is_staff` / `is_superuser`. Management CRUD lives
  under its own `/api/manage/` prefix, so the permission a URL needs is
  obvious from the URL.
- **Ownership scoping** - orders, addresses, reviews and merchant-owned
  records are filtered to the caller, so an id belonging to somebody else is
  simply not there.
- **Server-side money** - prices, tax and totals are never accepted from the
  client. Card numbers are never stored or logged; only the brand and last
  four digits are kept.
- **Atomic checkout** - product rows are locked with `SELECT … FOR UPDATE`, so
  two shoppers racing for the last unit cannot both succeed.
- **Rate limiting** - throttles on sign-in and registration, the contact form,
  newsletter signup and seller applications.
- **No account oracle** - "forgot password" answers the same way whether or
  not the address is registered.
- **Router guards on the client** are a convenience, not the boundary: hand
  editing a URL gets you a page shell and a `403`, not somebody else's data.

### ⚙️ Operations and deployment features

The parts that exist because this is a **Systems Deployment and Operations**
application rather than just a shop:

- **Runtime-configured frontend** - the API URL is read from
  `client/public/config.js` at page load, not baked into the bundle, so one
  built artifact deploys to every environment.
- **Health probes** - `GET /healthz/` (liveness, touches nothing) and
  `GET /readyz/` (readiness, checks the database and storage and returns
  `503` when either is down), both outside `/api/` and outside the auth stack.
- **Build identification** - `GET /api/version/` reports `APP_VERSION` and
  `GIT_COMMIT`, so you can tell which build a load balancer is serving.
- **Public runtime config** - `GET /api/config/` serves the tax rate and
  currency, so changing them does not mean rebuilding the frontend.
- **Split settings** - `dev` / `prod` modules selected by
  `DJANGO_SETTINGS_MODULE`, with everything else read from the environment
  (`django-environ`), including a single `DATABASE_URL`.
- **Pluggable media storage** - local disk by default, Amazon S3 by flipping
  `USE_S3` (`django-storages`). No AWS keys are read in code; boto3's default
  chain picks up an IAM instance role.
- **Pluggable email** - the console backend by default (reset and invitation
  links print into the server log), SMTP or Amazon SES purely through
  environment variables. Delivery failures are logged, never raised, so a slow
  mail server cannot fail a checkout.
- **Static file serving** - WhiteNoise with compressed, hashed manifests;
  gunicorn as the WSGI server.
- **Interactive API documentation** - OpenAPI 3 schema at `/api/schema/` and
  Swagger UI at `/api/docs/` (`drf-spectacular`).
- **Consistent error envelope** - every error response carries a `detail`
  string alongside the field-level errors, so the toast layer has exactly one
  place to read from.
- **Structured logging** - a single console-handler configuration with a
  `LOG_LEVEL` knob; health-probe noise is suppressed by default.
- **Seed data** - `python manage.py seed_demo` builds a deterministic
  catalogue: 15 categories, 15 brands, 47 photographed products and about 160
  reviews spread across one to five stars, plus optional demo member and
  merchant accounts. It is idempotent, so running it twice is safe.
- **Non-interactive admin creation** - `python manage.py create_admin`, from
  flags or `DJANGO_SUPERUSER_*` environment variables, for container
  entrypoints and Ansible tasks.

### 🗺️ The API surface at a glance

| Route                                                                                              | What lives there                                                   | Who may call it                          |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------- |
| `/api/auth/…`                                                                                   | register, login, refresh, logout, password forgot / reset / change | Public (change requires a token)         |
| `/api/products/`, `/api/products/{slug}/`, `/api/products/search/`                           | shop grid, product page, autosuggest                               | Public                                   |
| `/api/categories/`, `/api/brands/`                                                             | active categories and brands                                       | Public                                   |
| `/api/products/{slug}/reviews/`                                                                  | approved reviews plus the rating summary                           | Public                                   |
| `/api/config/`                                                                                   | tax rate, currency                                                 | Public                                   |
| `/api/contact/`, `/api/newsletter/subscribe/`                                                  | contact form, newsletter                                           | Public (throttled)                       |
| `/api/merchants/apply/`, `/api/merchants/signup/`                                              | seller application, invitation acceptance                          | Public (throttled)                       |
| `/api/users/me/`                                                                                 | own profile, read and update                                       | Any signed-in user                       |
| `/api/addresses/`                                                                                | own delivery addresses                                             | Owner only                               |
| `/api/orders/`                                                                                   | place, list, retrieve, cancel, update a line item                  | Owner; admins see every order            |
| `/api/reviews/`, `/api/wishlist/`                                                              | own reviews, wishlist toggle                                       | Owner                                    |
| `/api/manage/products/`, `/api/manage/brands/`                                                 | catalogue CRUD                                                     | Admin, or a merchant scoped to their own |
| `/api/manage/categories/`, `/api/manage/merchants/`, `/api/manage/reviews/`, `/api/users/` | categories, sellers, moderation, user list                         | Admin only                               |
| `/healthz/`, `/readyz/`, `/api/version/`                                                     | liveness, readiness, build id                                      | Public, no auth stack                    |
| `/api/schema/`, `/api/docs/`, `/admin/`                                                      | OpenAPI schema, Swagger UI, Django admin                           | Public / public / Django staff           |

## 🕧 Prerequisites

- **Python** 3.11 or later (3.12 or 3.13 recommended)
- **Node.js** 20 or later (22 LTS recommended)
- **PostgreSQL** 14 or later, running locally or on AWS RDS

## Architecture overview

```mermaid
graph TD
    Browser["🧑‍💻 Browser"] <-->|"Port 5173 dev / 80 prod"| Client["💻 Client - Vue 3 SPA"]
    Client <-->|"Port 8000 - REST over HTTP"| Server["🛠️ Server - Django REST Framework"]
    Server <-->|"Port 5432"| Database["🗄️ PostgreSQL"]
    Server <-->|"HTTPS - optional"| S3["🪣 S3 - product images"]
```

### Component connections

1. **Browser** - the customer, loading the single-page application.
2. **Client (Vue 3)** - static HTML, CSS and JavaScript. In development it is
   served by Vite on port `5173`. In production it is a folder of files served
   by any web server; there is no Node process in production.
3. **Server (Django + DRF)** - the REST API on port `8000`, run by gunicorn.
   All business rules and every authorisation decision live here.
4. **Database (PostgreSQL)** - port `5432`. Locally an installed server; in AWS
   an RDS instance.
5. **S3** *(optional)* - where uploaded product images go once you have more
   than one application server. Off by default.

> **Note:** these port numbers matter as soon as you split the tiers across
> containers or instances. Each one becomes a security group rule, a Compose
> port mapping or a Kubernetes service port.

### Two things that are different from a toy application, on purpose

**The frontend is configured at runtime, not at build time.** The API URL is
read from `client/public/config.js` when the page loads, not baked into the
JavaScript bundle. That means **one built artifact deploys to every
environment** - you edit a small text file on the server instead of rebuilding
the image. This is what makes a "build once, promote the same artifact" pipeline
possible, and it is worth understanding early.

**Database schema changes are a deploy step.** `python manage.py migrate` has to
run, in the right order, exactly once, before the new code starts serving
traffic. Where that command belongs in your pipeline - and what happens if it
fails halfway - is a genuine operational design decision.

## 📂 Project structure

```
client/                       # Vue 3 single-page application
  ├── .env.example            # build-time environment (deliberately almost empty)
  ├── index.html
  ├── vite.config.js
  ├── public/
  │   ├── config.js           # ← RUNTIME configuration. Read this file.
  │   └── images/
  └── src/
      ├── api/                # every API URL lives here, and nowhere else
      ├── components/         # common, layout, store and dashboard components
      ├── composables/
      ├── router/             # routes plus the role-based navigation guard
      ├── stores/             # Pinia state
      ├── styles/             # SCSS, Bootstrap 5 with the RMIT palette
      ├── utils/
      └── views/              # one component per page

server/                       # Django REST API
  ├── .env.example            # server environment variables - start here
  ├── manage.py
  ├── requirements.txt
  ├── config/
  │   ├── settings/
  │   │   ├── base.py         # shared configuration
  │   │   ├── dev.py          # development overrides
  │   │   └── prod.py         # production overrides - diff this against dev.py
  │   ├── urls.py             # /admin/, /healthz/, /readyz/, /api/
  │   ├── wsgi.py             # what gunicorn imports
  │   └── asgi.py
  ├── apps/
  │   ├── core/               # health probes, permissions, pagination, email
  │   ├── accounts/           # users, authentication, addresses
  │   ├── catalog/            # brands, categories, products
  │   ├── merchants/          # seller applications and approvals
  │   ├── orders/             # orders, order items, and payments.py
  │   └── reviews/            # reviews and wishlists
  ├── templates/email/        # the ten notification templates
  ├── seed_assets/products/   # 47 product photographs used by the seeder
  ├── media/                  # uploaded images (development only, gitignored)
  └── staticfiles/            # collectstatic output (gitignored)

README.md
.gitignore
```

---

## 📚 Recommended ways to deploy this, from easy to hard

### Plan A: run it locally

Follow "Plan A: build, configure and run locally" below.

### Plan B: one AWS EC2 instance

Put the database, the API and the frontend on a single instance. Follow
"Plan B: deploying on AWS EC2" below.

### Plan C: separate EC2 instances

1. Move PostgreSQL onto its own instance, or replace it with **AWS RDS**.
2. Put the API on one instance and the frontend on another.
3. Point the frontend at the API by editing `config.js` on the frontend
   instance - no rebuild required.
4. Add the API instance's origin to `CORS_ALLOWED_ORIGINS` on the server.
   *Discovering why this suddenly became necessary is the exercise.*
5. Open the right ports in each security group, and only the right ports. The
   database should not be reachable from the internet.

### Plan D: containerise with Docker

1. Write a `Dockerfile` for the API. Think about whether `migrate` and
   `collectstatic` belong in the image build or in the container's entrypoint.
2. Write a `Dockerfile` for the frontend. It should be a multi-stage build:
   Node compiles the bundle, then the result is copied into a web server image.
   **The final image must not contain Node.**
3. Decide how `config.js` gets into the frontend container at run time.
4. Run the containers on separate instances and get them talking.

### Plan E: Docker Compose

1. Write a `docker-compose.yml` describing the database, the API and the
   frontend.
2. Use a healthcheck against `/readyz/` so the API waits for the database
   rather than crash-looping.
3. Work out where migrations run when three containers start at once.

### Plan F: a real pipeline

Some directions worth taking:

1. **CI/CD** - use Jenkins to build, test and deploy automatically. Have the
   test suites you write emit machine-readable reports so Jenkins can publish
   them, and fail the build when they fail.
2. **Configuration management** - use Ansible to manage server configuration
   instead of running commands by hand.
3. **Infrastructure as code** - use AWS CloudFormation to provision the EC2
   instances, the RDS database, the S3 bucket and the IAM roles.
4. **Container orchestration** - deploy to Kubernetes or Docker Swarm and scale
   the API to more than one replica. **The moment you do, uploaded product
   images break** - see the note on `USE_S3` below. That is not a bug; it is the
   lesson.
5. **Monitoring** - Prometheus and Grafana. `/healthz/` and `/readyz/` are
   already there for probes; adding a metrics endpoint is your job.
6. **Load balancing** - put an AWS Elastic Load Balancer in front of two API
   instances. Use `/healthz/` as the target group health check, and read the
   `DisallowedHost` entry in Troubleshooting before you lose an afternoon to it.
7. **Zero-downtime deployment** - blue/green or canary. `GET /api/version/`
   returns the running build, so you can confirm which version is serving
   traffic from outside the box.
8. **Testing** - write the unit and integration suites for both tiers, then add
   end-to-end browser tests. The acceptance journeys in the Verification
   section are written to be converted into Playwright or Cypress specs.

**Step-by-step guides for Plan A and Plan B follow. Everything from Plan C
onwards is yours to build. 😊**

---

## 🔧 Plan A: build, configure and run locally

### Step 0: install Python, Node.js and PostgreSQL

- **Python** - [https://www.python.org/downloads/](https://www.python.org/downloads/) (3.11+)
- **Node.js** - [https://nodejs.org/en/download](https://nodejs.org/en/download) (20+)
- **PostgreSQL** - [https://www.postgresql.org/download/](https://www.postgresql.org/download/)
  - macOS: `brew install postgresql@16 && brew services start postgresql@16`
  - Ubuntu/Debian: `sudo apt install postgresql`
  - Windows: use the official installer, and let it start the service.

Verify all three:

```bash
python3 --version
node --version
psql --version
```

### Step 1: get the code

```bash
git clone <your-repository-url>
cd COSC2767-RMIT-Store-Django-Vue
```

### Step 2: create the database

**macOS (Homebrew)** - the installer gives your own account superuser rights, so
you can run `psql` directly:

```bash
psql -d postgres -c "CREATE ROLE rmit LOGIN PASSWORD 'rmit' CREATEDB;"
psql -d postgres -c "CREATE DATABASE rmit_store OWNER rmit;"
```

**Linux (Ubuntu, Debian, Fedora)** - there is no database role named after your
Linux account, so run these as the `postgres` system user instead:

```bash
sudo -u postgres psql -c "CREATE ROLE rmit LOGIN PASSWORD 'rmit' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE rmit_store OWNER rmit;"
```

**Windows** - open *SQL Shell (psql)* from the Start menu, accept the defaults,
enter the password you set during installation, and run the two `CREATE`
statements above without the `psql -c` wrapper.

Check it worked:

```bash
psql -U rmit -d rmit_store -c "SELECT version();"
```

If that asks for a password, enter `rmit`.

### Step 3: set up the API

```bash
cd server

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

Open `server/.env` and read it. The defaults work for local development, but
the comments explain what each variable is for and what it becomes in a real
deployment.

### Step 4: create the database tables

```bash
python manage.py migrate
```

This is the command that applies schema changes. Remember it - it has to run on
every deployment where the models have changed, before the new code starts
serving traffic.

### Step 5: load demo data

```bash
python manage.py seed_demo \
    --admin-email admin@rmit.edu.au \
    --admin-password 'RmitStore2767!' \
    --demo-users
```

That creates:

|                                       |                                                                 |
| ------------------------------------- | --------------------------------------------------------------- |
| 15 categories, 16 brands, 47 products | one per photograph, with matching reviews                       |
| An administrator                      | `admin@rmit.edu.au` / the password you chose                  |
| A demo member                         | `member@rmit.edu.au` / `DemoPass2767!`                      |
| A demo seller                         | `merchant@rmit.edu.au` / `SellerPass2767!`, with 5 products |

The command is **idempotent** - running it twice will not duplicate anything.
Add `--flush` to wipe the catalogue and start over, or `--no-images` to skip the
photographs and finish in a couple of seconds.

The catalogue is curated rather than generated, and lives in
`server/apps/core/management/commands/_seed_catalog.py`. Each of the 47
product photographs is a real piece of RMIT merchandise, and each one is
described, priced, categorised and reviewed as itself - so the store you deploy
reads like a store. Every student gets an identical catalogue.

The sixteenth brand is `Campus Threads`, which belongs to the demo seller
rather than the store, and holds the five products above.

### Step 6: run the API

```bash
python manage.py runserver 0.0.0.0:8000
```

Check it:

```bash
curl http://localhost:8000/healthz/     # {"status": "ok"}
curl http://localhost:8000/readyz/      # {"database": "ok", "storage": "ok"}
```

Then open these in a browser:

- [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) - interactive API documentation. **You can
  exercise the entire backend from here without the frontend running at all.**
- [http://localhost:8000/admin/](http://localhost:8000/admin/) - the Django admin, signed in with the
  administrator account you just created. Useful for inspecting data during a
  deployment.

This is `/api/docs/`. Every endpoint in the table above is here, and each one
can be called from the browser with the **Try it out** button.

![Swagger UI listing the RMIT Store API endpoints grouped by tag](screenshots/swagger-ui.png)

This is `/admin/`. Sign in with the administrator account from Step 5.

![The Django admin login form](screenshots/django-admin-login.png)

![The Django admin index listing the accounts, catalog, merchants, orders and reviews apps](screenshots/django-admin.png)

> If `/admin/` renders as unstyled black-on-white text, that is `collectstatic`
> not having run. It does not matter yet under `runserver` with `dev` settings,
> and it matters a great deal in **9.3**.

This command holds the terminal open and does not return - that is your **first
terminal**, and the API keeps running in it. Leave it alone and open a second
one for the next step.

### Step 7: run the frontend

Leave the API running in the first terminal and open a **second terminal**. A
new terminal starts in your home directory, so change into the repository
first:

```bash
cd /path/to/COSC2767-RMIT-Store-Django-Vue/client
npm install
cp .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). If everything above worked, this is what you get

- and the product photography loading is the proof that the API, the database
  and the seeded media are all reachable from the browser.

![The RMIT Store home page running on localhost:5173](screenshots/homepage.png)

If the page loads but every product is a grey placeholder box, the SPA is
running and the API is not. Check the terminal from Step 6, then read
"The frontend loads but every request fails" in Troubleshooting.

The Vite dev server proxies `/api` and `/media` through to
`http://localhost:8000`, so the browser sees a single origin and cross-origin
requests never come up. This mirrors the web server configuration you will write
for a real deployment. If port 8000 is taken on your machine, set
`VITE_DEV_API_PROXY` in `client/.env` to wherever the API actually is.

### Step 8: build the frontend the way you would deploy it

Running `npm run dev` is not deployment. Before you go near EC2, see what the
real artifact looks like:

From the `client/` directory:

```bash
npm run build            # produces client/dist/
npx vite preview --port 4173
```

`client/dist/` is a folder of static files. **That folder is what you deploy.**
There is no Node process in production.

Now do the thing that makes the whole deployment story work. Still in `client/`:

```bash
# Point the built artifact at a different API without rebuilding it
nano dist/config.js       # change API_BASE_URL to http://localhost:8000/api
```

Hard-reload [http://localhost:4173](http://localhost:4173) with the browser's network tab open. The
requests for `/api/products/` now go to `http://localhost:8000/api/products/`
instead, the page works exactly as before, and **the hashed bundle filename in
`dist/assets/` has not changed** - it is byte-for-byte the same artifact.

That is the whole trick. Remember it when you get to Plan C.

> One thing to be aware of while you are testing: `vite preview` reuses the dev
> server's proxy, so the default relative `"/api"` already works there. That is
> why the instruction above is to watch *where the requests go* rather than
> whether the page loads - on a real static web server there would be no proxy
> unless you configured one.

---

## ☁️ Plan B: deploying on AWS EC2 (single instance)

> **Stay as `ec2-user` the whole way through.** Amazon Linux logs you in as
> `ec2-user`, and that is the account every instruction below assumes: the
> checkout lives in `/home/ec2-user/`, the systemd unit in **9.3** runs as
> `User=ec2-user`, and the two nginx `alias` paths in **9.4** point into
> `/home/ec2-user/`. Do **not** run `sudo su -` or `sudo -i` to become `root`.
> If you do, the clone lands in `/root/`, which nginx cannot traverse into no
> matter how you `chmod` it, gunicorn starts as the wrong user, and you get a
> `403` on every product image with nothing obviously wrong to find.
>
> Use `sudo` for the individual commands that need it - and those commands are
> already written with `sudo` in front of them below. Anything without `sudo`
> is meant to run as `ec2-user`. Check who you are at any point with:
>
> ```bash
> whoami          # should print: ec2-user
> pwd             # should be under /home/ec2-user
> ```
>
> If `whoami` says `root`, type `exit` to drop back to `ec2-user` before
> continuing.

### Step 1: launch an instance

- **AMI:** Amazon Linux 2023
- **Type:** `t3.small` is comfortable. `t3.micro` works, but the frontend build
  is memory-hungry - see the troubleshooting note below.
- **Security group inbound rules:**

| Port | Source             | Why                          |
| ---- | ------------------ | ---------------------------- |
| 22   | My IP              | SSH                          |
| 8000 | Anywhere (for now) | the API                      |
| 5173 | Anywhere (for now) | the frontend dev server      |
| 80   | Anywhere           | nginx, once you reach Step 9 |

Do **not** open 5432 to the world. If you need to reach the database from your
laptop with a GUI client, scope that rule to **My IP** only.

### Step 2: install the runtimes

```bash
sudo dnf update -y
sudo dnf install -y git python3.11 python3.11-pip postgresql16 postgresql16-server

# Node.js 22
curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
sudo dnf install -y nodejs

python3.11 --version && node --version
```

### Step 3: install and start PostgreSQL

```bash
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql

sudo -u postgres psql -c "CREATE ROLE rmit LOGIN PASSWORD 'rmit' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE rmit_store OWNER rmit;"
```

By default PostgreSQL only accepts connections from the local machine, which is
exactly what you want while everything is on one instance.

#### Allow password logins over localhost

**Do not skip this.** On Red Hat family systems, including Amazon Linux, a fresh
`initdb` writes a `pg_hba.conf` that uses **`ident`** authentication for
connections to `127.0.0.1`. Django connects over TCP with a username and
password, so it is refused:

```
django.db.utils.OperationalError: connection to server at "localhost" (127.0.0.1),
port 5432 failed: FATAL:  Ident authentication failed for user "rmit"
```

Switch those two lines to `scram-sha-256` and reload:

```bash
# Change the auth method on every TCP ("host") line from ident to scram-sha-256.
# The "local ... peer" lines are left alone - that is what `sudo -u postgres
# psql` uses, and breaking it would lock you out of the database entirely.
sudo sed -i 's/^\(host.*\)ident$/\1scram-sha-256/' /var/lib/pgsql/data/pg_hba.conf

sudo systemctl reload postgresql
```

Confirm the change took, then confirm you can actually log in with a password:

```bash
grep '^host' /var/lib/pgsql/data/pg_hba.conf     # should say scram-sha-256
PGPASSWORD=rmit psql -h 127.0.0.1 -U rmit -d rmit_store -c "SELECT 1;"
```

If that `SELECT 1` works, Django will connect. If it does not, fix it here -
every later step depends on it.

> Note this affects your laptop too, if you installed PostgreSQL from a Red Hat
> family package. macOS Homebrew and the Debian/Ubuntu packages already permit
> password logins on localhost, which is why Plan A does not mention it.

### Step 4: get the code and install dependencies

Clone into `ec2-user`'s home directory - `/home/ec2-user/` is where every path
later in this guide expects to find it:

```bash
cd ~
git clone <your-repository-url>
cd COSC2767-RMIT-Store-Django-Vue

cd server
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 5: configure the API

```bash
cp .env.example .env
nano .env
```

> `nano` saves with **Ctrl-O** then Enter, and exits with **Ctrl-X**. It is
> installed on Amazon Linux 2023 by default; if it is missing, run
> `sudo dnf install -y nano`.

Change at least these:

```env
SECRET_KEY=<generate a real one - see the comment in the file>
ALLOWED_HOSTS=<your-ec2-public-ip>,localhost,127.0.0.1
CLIENT_URL=http://<your-ec2-public-ip>:5173
CORS_ALLOWED_ORIGINS=http://<your-ec2-public-ip>:5173
DATABASE_URL=postgres://rmit:rmit@localhost:5432/rmit_store
```

> **Use `localhost` in `DATABASE_URL`, not the public IP**, when the database is
> on the same instance. Routing a connection out to the internet and back to the
> same machine is slower and usually blocked.

### Step 6: migrate and seed

```bash
python manage.py migrate
python manage.py seed_demo --admin-email admin@rmit.edu.au \
                           --admin-password 'RmitStore2767!' --demo-users
```

### Step 7: run the API

This is your **first terminal**. The command below does not return - it holds
the terminal open and prints a log line per request, which is exactly what you
want while you are getting things working.

```bash
python manage.py runserver 0.0.0.0:8000
```

Check `http://<your-ec2-public-ip>:8000/healthz/` from your own browser.

**Leave this running.** Do not press Ctrl-C, and do not close the window - the
frontend in Step 8 has nothing to talk to without it. Open a **second SSH
terminal** for the next step.

> **`runserver` is a development server.** It is single-threaded, it does not
> serve static files efficiently, and the Django documentation says plainly not
> to use it in production. It is fine for getting Plan B working. Moving to
> gunicorn behind nginx, managed by systemd, is your next step:
>
> ```bash
> python manage.py collectstatic --noinput
> gunicorn config.wsgi:application \
>     --bind 0.0.0.0:8000 --workers 3 \
>     --env DJANGO_SETTINGS_MODULE=config.settings.prod
> ```
>
> **Expect every product image to 404 the moment you do this**, and do not go
> looking for the bug - there isn't one. `config/urls.py` serves `/media/`
> only while `DEBUG` is true, because handing uploaded files out of the WSGI
> process is a web server's job rather than Django's. Under gunicorn nothing
> is serving them yet; Step 9 is where nginx picks the job up.
>
> The admin's own styling keeps working, because `collectstatic` plus
> whitenoise covers `/static/`. Static files and media files are two different
> problems with two different answers, and this is the moment that stops being
> an abstract distinction.
>
> Run it in the foreground here if you want to see it work; **9.3** turns the
> same command into a systemd service bound to `127.0.0.1` instead.

### Step 8: run the frontend

**Open a second terminal on your own machine and SSH into the instance again**,
exactly the way you did the first time:

```bash
ssh -i <your-key>.pem ec2-user@<your-ec2-public-ip>
```

You now have two terminals connected to the same instance: the **first** is
running the API from Step 7, the **second** is about to run the client. A fresh
SSH session lands in `/home/ec2-user`, and it is a fresh shell - so the
virtualenv you activated in Step 4 is not active here. That is fine; the client
is a Node project and does not need it.

In this second terminal:

```bash
cd ~/COSC2767-RMIT-Store-Django-Vue/client
npm install
cp .env.example .env
npm run dev -- --host 0.0.0.0
```

Open `http://<your-ec2-public-ip>:5173`.

This command also holds its terminal open, so from here on you have two
long-running processes in two terminals. To stop either one, press Ctrl-C in
the terminal it is running in.

### Step 9: serve the frontend properly

Steps 7 and 8 got the application running. Neither is a deployment: `runserver`
is single-threaded, `npm run dev` is a build tool, and both die when you close
the SSH session.

Now do it the way you actually would. Six sub-steps, in this order - each one
depends on the one before it.

- **9.1** Build the SPA and install nginx
- **9.2** Reconfigure the API for production
- **9.3** Run the API under gunicorn and systemd
- **9.4** Configure nginx
- **9.5** Verify
- **9.6** Close the ports you no longer need

The finished shape: **nginx owns port 80** and is the only thing the internet
talks to. It serves the built SPA from disk, serves uploaded images from disk,
and reverse-proxies everything Django-shaped to gunicorn on `127.0.0.1:8000`.
The browser sees **one origin**, so CORS never enters the picture.

#### 9.1 Build the SPA and install nginx

In your **second terminal**, press Ctrl-C to stop `npm run dev` - you are about
to replace it with a real build. Then, from
`~/COSC2767-RMIT-Store-Django-Vue/client`:

```bash
npm run build

sudo dnf install -y nginx
sudo systemctl enable --now nginx

sudo cp -r dist/* /usr/share/nginx/html/
```

Browse to `http://<your-ec2-public-ip>/`. The page loads and nothing else
works, because nothing is proxying `/api/` yet. That is expected.

> `dist/config.js` keeps its default `API_BASE_URL: "/api"` - nginx is about to
> put the API on the same origin. If you changed it while debugging, change it
> back, and remember the copy that matters is now
> `/usr/share/nginx/html/config.js`.

#### 9.2 Reconfigure the API for production

Edit `server/.env` - `nano ~/COSC2767-RMIT-Store-Django-Vue/server/.env`:

```env
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=<generate one - see below>
ALLOWED_HOSTS=<your-ec2-public-ip>,127.0.0.1,localhost
CLIENT_URL=http://<your-ec2-public-ip>
CORS_ALLOWED_ORIGINS=http://<your-ec2-public-ip>
CSRF_TRUSTED_ORIGINS=http://<your-ec2-public-ip>
DATABASE_URL=postgres://rmit:rmit@localhost:5432/rmit_store

# You are still on plain HTTP. prod.py defaults both of these to True, and a
# secure cookie is never sent over http:// - so the admin login would accept
# your password and bounce you straight back to the login form. Turn them on
# again the day you terminate TLS.
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

Generate a real key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

`CLIENT_URL` is what builds the links in outgoing email. It has been pointing
at port 5173 since Step 5, so leaving it there would send the seller invitation
in journey E to a dev server you are about to stop.

#### 9.3 Run the API under gunicorn and systemd

Press Ctrl-C in the **first terminal** to stop the `runserver` from Step 7 -
systemd is about to own the API instead. Then, in that same terminal, from
`server/` with the virtualenv active:

```bash
python manage.py collectstatic --noinput
```

Not optional: `config.settings.prod` uses whitenoise's manifest storage, which
raises rather than quietly serving nothing when the manifest is missing.

```bash
sudo nano /etc/systemd/system/rmit-api.service
```

```ini
[Unit]
Description=RMIT Store API (gunicorn)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/COSC2767-RMIT-Store-Django-Vue/server
ExecStart=/home/ec2-user/COSC2767-RMIT-Store-Django-Vue/server/.venv/bin/gunicorn \
    config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --env DJANGO_SETTINGS_MODULE=config.settings.prod \
    --access-logfile - --error-logfile -
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rmit-api
systemctl status rmit-api
```

Three details worth the ink:

- **`--bind 127.0.0.1:8000`, not `0.0.0.0:8000`.** Once nginx is in front,
  gunicorn has no business being reachable from anywhere else. The security
  group is your second line of defence, not your first.
- **`DJANGO_SETTINGS_MODULE` goes on the command line**, not in `.env`.
  `config/wsgi.py` chooses the settings module before django-environ has read
  the file, so setting it there is too late.
- **Logs move.** The console emails from journey E now appear in
  `journalctl -u rmit-api -f`, not in a terminal you are watching.

#### 9.4 Configure nginx

```bash
sudo nano /etc/nginx/conf.d/rmit-store.conf
```

```nginx
server {
    listen       80 default_server;
    listen  [::]:80 default_server;
    server_name  _;

    root  /usr/share/nginx/html;
    index index.html;

    # Product photographs are larger than nginx's 1M default, which would 413.
    client_max_body_size 10M;

    # --- The SPA -----------------------------------------------------------
    # History-mode routing: an unknown path is a Vue route, not a missing file,
    # so fall back to index.html or a refresh on /shop returns 404.
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Runtime config must never be cached, or editing API_BASE_URL on the
    # server does nothing until every browser hard-reloads.
    location = /config.js {
        add_header Cache-Control "no-store";
    }

    # Hashed bundle filenames are immutable by construction.
    location /assets/ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # --- Django --------------------------------------------------------
    # /api/ is what the SPA calls. /admin/ and the two probes are included
    # because you are about to close port 8000 and would otherwise lose them.
    location ~ ^/(api|admin|healthz|readyz)(/|$) {
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Host  $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # --- Uploaded product images -------------------------------------------
    location /media/ {
        alias /home/ec2-user/COSC2767-RMIT-Store-Django-Vue/server/media/;
        access_log off;
        expires 7d;
    }

    # --- Django's own static files: admin CSS, DRF, Swagger ----------------
    location /static/ {
        alias /home/ec2-user/COSC2767-RMIT-Store-Django-Vue/server/staticfiles/;
        access_log off;
        expires 7d;
    }
}
```

> **Check the two `alias` paths against your own checkout before you reload.**
> They are the only absolute paths in this entire guide, and they are wrong
> unless your repository root happens to *be* the `COSC2767-RMIT-Store-Django-Vue`
> directory. If the app sits in a subdirectory of your repo, there is an extra
> level. Ask the filesystem rather than guessing:
>
> ```bash
> find /home/ec2-user -type d -path '*/server/media/products'
> ```
>
> Everything up to `/server/media/` is what belongs in the `/media/` alias, and
> the same parent with `/server/staticfiles/` belongs in the `/static/` one.

Then let nginx traverse to the media directory, check the syntax and reload:

```bash
chmod o+x /home/ec2-user
sudo nginx -t
sudo systemctl reload nginx
```

> **If `nginx -t` says `duplicate default server`**, the stock config has its
> own port-80 block. Open `/etc/nginx/nginx.conf`, comment out the `server { ... }` block containing `root /usr/share/nginx/html;`, and try again.

Four decisions in that file are the actual lesson:

- **`proxy_set_header Host $host` is load-bearing.** `proxy_pass` sends
  `Host: $proxy_host` by default, so Django would see `Host: 127.0.0.1:8000`
  and `request.build_absolute_uri()` would return every `image_url` as
  `http://127.0.0.1:8000/media/...` - an address that resolves to the
  *browser's* machine. Every product image breaks, with a CORS error about a
  "more-private address space" that has nothing to do with CORS.
  `config.settings.prod` sets `USE_X_FORWARDED_HOST = True`, so under gunicorn
  it is `X-Forwarded-Host` that Django reads; set both and you are covered
  either way. Whichever host you forward must be in `ALLOWED_HOSTS`.
- **`/media/` is served from disk, not proxied.** Under gunicorn Django returns
  404 for uploaded images (see the note in Step 7), so forwarding `/media/` to
  port 8000 forwards you to a 404. Needing `chmod o+x` on a home directory to
  make this work is the argument for `USE_S3`.
- **`/static/` needs its own block.** Without it `location /` answers with
  `index.html` and `/admin/` renders unstyled. Static files and media files are
  two different problems, and this is the second time that has bitten.
- **`/healthz/` and `/readyz/` are proxied deliberately.** They are your only
  view of the API's health once port 8000 is shut, and in Plan F they become
  the load balancer's target group check.

#### 9.5 Verify

```bash
IP=<your-ec2-public-ip>

curl -I  http://$IP/                 # 200, text/html
curl -s  http://$IP/healthz/         # {"status": "ok"}
curl -s  http://$IP/readyz/          # {"database": "ok", "storage": "ok"}
curl -sI http://$IP/shop             # 200, not 404 - the SPA fallback works
curl -s  http://$IP/api/products/ | grep -o '"image_url":"[^"]*"' | head -1
```

That last command is the one to read carefully. It must print a URL on **your
public IP with no port** - `http://<ip>/media/products/....jpg`. Anything
mentioning `localhost` or `127.0.0.1:8000` means the `Host` header is not
reaching Django. Fetch the file itself to be sure:

```bash
curl -I http://$IP/media/products/<one-of-those-filenames>.jpg   # 200
```

| Symptom                | Cause                                                                                  |
| ---------------------- | -------------------------------------------------------------------------------------- |
| `404` on `/media/` | the`alias` path does not match your checkout, or `seed_demo` never wrote the files |
| `403` on `/media/` | `chmod o+x /home/ec2-user` did not happen                                            |
| `502` on `/api/`   | gunicorn is down -`journalctl -u rmit-api -n 50`                                     |
| `400` on `/api/`   | the public IP is missing from`ALLOWED_HOSTS`                                         |
| `/admin/` unstyled   | `collectstatic` did not run, or the `/static/` alias is wrong                      |
| Admin login loops      | `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` still True                          |

For anything nginx serves off disk, stop guessing and read the path it actually
tried:

```bash
sudo tail -5 /var/log/nginx/error.log
```

Then walk journeys A and B from the Verification section. They exercise the
image path, the API path and the database in one pass.

#### 9.6 Close the ports you no longer need

Everything now arrives on port 80, so in the security group **remove the
inbound rules for 8000 and 5173**. Keep 22 and 80.

Re-run the checks in 9.5 afterwards - they all go through port 80, so they
should all still pass. If one of them only worked because you were quietly
reaching port 8000, this is where you find out.

---

## 🖼️ Product images and the S3 exercise

By default, uploaded product images are written to `server/media/` on the local
disk of whichever machine is running the API. That works perfectly - right up
until you run a second application server.

Then a merchant uploads an image, it lands on instance A, and every request the
load balancer sends to instance B returns a 404. Half your product images
break, intermittently, in a way that looks like a caching bug. It is not; it is
what happens when state lives on an instance.

With S3 enabled, those same uploads go to a bucket instead. Every instance
reads and writes one shared store, the images survive an instance being
replaced, and the problem disappears - with no code change, because the storage
backend is selected by configuration.

Creating the bucket, deciding how the browser is allowed to read from it, and
giving the instance an identity that can write to it **without long-lived
access keys sitting in a `.env` file** is your exercise. Doing it once by hand
makes writing the CloudFormation template for it considerably easier.

## 💳 Paying for an order

Checkout takes a card, but the gateway behind it is simulated. There is no
payment provider, no account, no API key and no outbound network call - so
there is nothing to configure, and nothing that can fail in CI or on a private
subnet.

The card numbers are Stripe's, so they are probably the ones you already know:

| Card number             | What happens                                 |
| ----------------------- | -------------------------------------------- |
| `4242 4242 4242 4242` | Approved (Visa)                              |
| `5555 5555 5555 4444` | Approved (Mastercard)                        |
| `3782 822463 10005`   | Approved (American Express, four-digit code) |
| `4000 0000 0000 0002` | Declined - card declined                     |
| `4000 0000 0000 9995` | Declined - insufficient funds                |
| `4000 0000 0000 0069` | Declined - expired card                      |
| `4000 0000 0000 0127` | Declined - incorrect security code           |
| `4000 0000 0000 0119` | Declined - processing error                  |

Any expiry date in the future and any security code of the right length will
do. The card form in the bag keeps the common numbers behind a *use a test
number* disclosure, so demonstrating a checkout needs no typing - open it and
click a number to fill the whole form.

![The checkout card form with the use a test number disclosure expanded, showing the succeeds, declined and insufficient funds buttons](screenshots/checkout-card-form.png)

Pay with `4000 0000 0000 0002` and you get this. **Look at what did not
happen:** both items are still in the bag, and no stock has moved.

![The bag after a declined payment, showing the Your card was declined message with both items still in the bag](screenshots/payment-declined.png)

A declined card leaves no order behind and takes no stock, which makes the
decline numbers a safe thing to try repeatedly while verifying a deployment.

Pay again with `4242 4242 4242 4242` and the order is placed.

![The order confirmation page shown after a successful payment](screenshots/order-confirmation.png)

## 📧 Email

The application sends transactional email: welcome messages, password resets,
order confirmations, seller applications and invitations, contact-form and
newsletter notifications.

Out of the box it needs no mail server. Messages are written to the API
server's log instead of being delivered, so the password-reset and
seller-invitation flows - both of which depend on a link - can still be
completed on a machine with nothing configured. The links appear in the
terminal running the API.

Pointing it at real delivery, whether Amazon SES or any other SMTP host, is a
configuration change rather than a code change. Doing that, and keeping the
credentials somewhere that is not the repository, is left to you.

> Delivery failures are logged, never raised, so that a slow mail server cannot
> fail a checkout. The consequence is that **a broken mail configuration is
> silent** - the interface says "check your email" either way. Never conclude
> that mail works because a page said it did.

## 🩺 Health checks

| Endpoint              | Question it answers                                                                        | Use it for                                                                  |
| --------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| `GET /healthz/`     | Is the process alive? Touches nothing.                                                     | ELB target group check, Kubernetes`livenessProbe`                         |
| `GET /readyz/`      | Can it serve useful traffic? Checks the database and storage. Returns**503** if not. | Kubernetes`readinessProbe`, Compose `depends_on`, an Ansible smoke test |
| `GET /api/version/` | Which build is running?                                                                    | Verifying a blue/green or canary cutover from outside                       |

The distinction matters. A liveness probe that checks the database will restart
a perfectly healthy application server because the database was briefly slow -
turning a small outage into a restart loop. Readiness takes an instance out of
rotation without killing it, so it can recover and rejoin.

## 🧪 Tests

**This repository ships with no test suite. Writing it is your job.**

There are no unit tests, no integration tests and no end-to-end tests here -
not because the application does not deserve them, but because building them is
part of the assessment. The tooling, the structure, the coverage target and how
the suites run in your pipeline are all yours to choose, and to justify.

Worth aiming at: authorisation (who may call what), server-side pricing and
tax, the stock decrement on checkout, and what a declined card leaves behind.
That is where the bugs worth catching live.

The acceptance journeys in the next section are a ready-made backlog - each one
converts into an end-to-end test.

## 🔍 Verifying a deployment

After every deployment, walk these. They are also your backlog for automated
end-to-end tests.

Every screen these journeys end on is pictured in the **Features** section
above, so you can compare what you are looking at against what it should be.
The screenshots live in [`screenshots/`](screenshots/).

**A. Anonymous browsing.** Home → Shop shows 12 of 47 products → narrow the
price range and watch the count drop → choose "4 ★ & up" → sort by price,
high to low, and check it is actually descending → page 2 shows different
products → open one and confirm the image, price, stock and star summary.

**B. Register and buy.** Create an account → add two products, one taxable and
one not → open the bag and check the running total → pay with the declined
test card `4000 0000 0000 0002` and confirm you get a decline, **the bag still
has your items in it, and no stock has moved** → pay again with
`4242 4242 4242 4242` → confirm the order number → open the order and **check
the arithmetic by hand**: 5% tax on the taxable line only → confirm the summary
shows *Visa ending 4242* and *Paid* → confirm in `/admin/` that stock went down
by exactly the right amount, once.

A finished journey B looks like this. One taxable line at `$44.95` and one
non-taxable at `$27.95`: subtotal `$72.90`, tax `$2.25` - five per cent of the
t-shirt alone, not of the subtotal - and a total of `$75.15`.

![An order detail page showing subtotal $72.90, sales tax $2.25, total $75.15, Visa ending 4242 and a Paid badge](screenshots/order-detail.png)

**C. Fulfilment.** As an administrator, mark an item *Shipped* → the customer
sees it. As the customer, cancel the other item → its stock comes back and the
order total drops. Cancel the last item → the order becomes **Cancelled but is
still there**, and the payment reads *Refunded*. That is deliberate: deleting
an order destroys the customer's purchase history. Now try to move a cancelled
item back to *Processing* as an administrator → the dropdown is disabled,
because the stock has already gone back and the money has already been
returned.

**D. Reviews and wishlist.** Post a review → it appears immediately and the
star rating updates → an administrator rejects it → it disappears from the
product page *and* the average recomputes → heart a product → it shows in your
wishlist and the heart stays filled on the shop grid → sign out and confirm the
hearts are empty with no errors in the console.

**E. The seller lifecycle - the big one.** Submit the `/sell` form → an
administrator sees it as *Waiting Approval* → **Approve** → the invitation email
appears in the API server's log → open the `/merchant-signup/...` link, set a
password, and land signed in as a seller → the dashboard menu is shorter (no
Users, Categories, Sellers or Reviews) → **the brand exists but is inactive**,
so add a product and confirm it does *not* appear in the shop → an administrator
activates the brand → now it appears → the seller's product list shows only
their own products → an administrator deactivates the seller → they see the
disabled-account screen and their products vanish from the shop.

**F. Administration.** Create, edit, deactivate and delete one of each:
category (use the product multi-select and confirm it round-trips), brand,
product (upload a real image and confirm it renders). Search the user list.

## 🧯 Troubleshooting

**`connection refused` on port 5432** - PostgreSQL is not running.
`sudo systemctl status postgresql`, or `brew services list` on macOS.

**`relation "catalog_product" does not exist`** - you skipped `migrate`.

**The frontend loads but every request fails** - check `config.js`. Open the
browser's network tab and look at where the requests are actually going. In
development, check that the API is on the port `VITE_DEV_API_PROXY` expects.

**`DisallowedHost` or a 400 from a health check** - a load balancer health check
arrives with a `Host` header of the instance's *private* IP. If that is not in
`ALLOWED_HOSTS`, Django answers **400** and the target group marks a perfectly
healthy instance unhealthy. Add the private IP or `.compute.internal`, or
configure the check to send a `Host` header you have allowed. `dev` settings use
`['*']`, so this never bites before Plan F - and it is the single most common
way to lose an afternoon on it.

**`npm run build` is killed on a `t3.micro`** - the build ran out of memory. Add
swap, use a larger instance, or (best) build in CI and ship only the resulting
`dist/` folder to the server. That last option is the right answer, and it is
also the point of having a build stage.

**Every product image is broken on EC2, with a CORS error naming
`localhost:8000` and a "more-private address space `loopback`"** - the API is
fine; it is being told the wrong hostname. `image_url` is absolute, built by
`request.build_absolute_uri()` from the incoming **`Host` header**
(`server/apps/core/serializers.py`), so whatever hostname reaches Django is the
hostname your browser is sent back to. A proxy that rewrites `Host` to its own
target therefore hands the browser `http://localhost:8000/media/...`, which
resolves to the machine the browser is running on. On a laptop that is
accidentally the right answer, which is why Plan A never shows the fault.

Confirm it in one line - same server, same database, two different `Host`
headers:

```bash
curl -s http://<ec2-ip>:8000/api/products/ | grep -o '"image_url":"[^"]*"' | head -1
curl -s http://<ec2-ip>:5173/api/products/ | grep -o '"image_url":"[^"]*"' | head -1
```

Fix it wherever the rewrite happens: `changeOrigin: false` in
`client/vite.config.js` for the dev server, or `proxy_set_header Host $host;`
in nginx (Step 9). Serving both tiers through one origin makes the whole class
of problem disappear, which is the actual lesson.

**Product images 404 after scaling to two instances** - working as designed.
See the S3 section above.

**Static files missing from `/admin/` under gunicorn** - run
`python manage.py collectstatic --noinput`.

**`403` on every image and asset, and your checkout is in `/root/`** - you ran
`sudo su -` somewhere in Plan B and cloned the repository as `root`. `/root` is
mode `0700` and nginx runs as an unprivileged user, so it cannot traverse into
it; `chmod o+x /root` would "fix" it by opening the root account's home
directory to every process on the box, which is not a fix. Move the checkout to
where the guide expects it, as `ec2-user`:

```bash
sudo mv /root/COSC2767-RMIT-Store-Django-Vue /home/ec2-user/
sudo chown -R ec2-user:ec2-user /home/ec2-user/COSC2767-RMIT-Store-Django-Vue
```

Then recreate the virtualenv (`python3.11 -m venv .venv` - the old one has
`/root` baked into its scripts), and re-check the `WorkingDirectory` and
`ExecStart` paths in `rmit-api.service` and the two `alias` paths in
`rmit-store.conf`.

## 🔐 Developer notes

- The API and the frontend are fully independent. Each can be developed,
  tested, built and deployed on its own - which is what makes Plans C through F
  possible.
- Every authorisation decision is made on the server. The frontend's route
  guard decides what to *render*, not what you are allowed to *see*; hand-edit
  a URL and you will get a page shell and a 403, not somebody else's data.
- The API denies by default. A new endpoint requires authentication unless it
  explicitly opts out - so a forgotten permission fails closed.
- `/api/docs/` is the fastest way to explore the backend, and it works before
  the frontend exists.

## 🏆 Author

- Tom Huynh - tomhuynhsg@gmail.com
