# Bookstore

An online bookstore built for Nepal — browse books and order with Cash on Delivery. Staff manage catalog, categories, and orders from a built-in admin dashboard.

## Who it's for

- **Shoppers** — browse the catalog, add books to a cart, check out in minutes, and track orders from "Pending" to "Delivered".
- **Store admins** — manage books and categories, see sales at a glance, and mark orders delivered.
- **Developers** — a Django codebase with typed frontend flows, Dockerized Postgres/Redis, and 53 automated tests.

## Feature tour

### Shopping
- Homepage with latest arrivals, paginated catalog, and book detail pages.
- Cart with per-user uniqueness (no duplicates, race-safe) and one-click checkout.
- Orders are **Cash on Delivery**, protected by hCaptcha at checkout. Online gateways (eSewa/Khalti) are shelved for now — see Roadmap.
- "My Orders" with live status badges; exact Decimal pricing (2 × Rs 19.99 = Rs 39.98, always).

### Store admin (`/admin/`)
- Dashboard with real counts: delivered/pending orders, customers, in-stock books, categories, admins.
- Book CRUD with cover uploads (local disk or **S3**), category CRUD with deletion protection — a category with books can't be wiped by accident.
- Order board with staff-only "Mark as Delivered"; customer list with pagination.

### Auth & security
- Site sign-in/sign-up with Django sessions: throttled password login, role-based redirects (shoppers home, staff to dashboard), POST-only logout.
- All destructive actions are POST-only with CSRF; deleting a category with books fails with a clear message instead of cascading.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Django 5.1 (Python 3.12), three apps: `books`, `accounts`, `userpage` |
| Frontend | Server-rendered templates + Bootstrap 5, crispy-forms, vanilla JS |
| Auth | Django sessions (throttled login) + hCaptcha on checkout |
| Data | Postgres (Docker) with SQLite fallback for local dev |
| Cache/sessions | Redis via `django-redis`, locmem fallback |
| Media | Local `media/` or S3 (`USE_S3=1`) |
| Prod server | Gunicorn + WhiteNoise, `collectstatic` in the Docker build |
| Tests | Django test suite covering auth, catalog, cart, orders |

## Quickstart

### Option A — Docker (recommended, full stack)

```bash
cp .env.example .env   # set SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

This starts web (auto-reload dev server), Postgres 16, and Redis 7. Open http://localhost:8000 (or `$WEB_PORT`).

For production serving, remove the `command:` override in `docker-compose.yml` to use Gunicorn.

### Option B — Local Python

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

SQLite is used automatically when `POSTGRES_DB` is unset.

## Configuration (`.env`)

| Key | Purpose | Default |
|---|---|---|
| `SECRET_KEY` / `DEBUG` / `ALLOWED_HOSTS` | Django core | dev fallback / `1` / empty |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | Postgres (compose sets host `db`) | SQLite when `POSTGRES_DB` unset |
| `REDIS_URL` | Redis cache + sessions | locmem |
| `USE_S3`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_LOCATION` | S3 cover uploads | local `media/` |
| `HCAPTCHA_SITEKEY`, `HCAPTCHA_SECRET` | hCaptcha on checkout | off |

## Project structure

```
accounts/    site auth (throttled login, registration, checkout hCaptcha), auth tests
books/       admin catalog: books/categories CRUD, dashboard, orders, customers
userpage/    storefront: homepage, catalog, cart, orders, deliver flow
bookstore/   settings (env-driven), urls, wsgi
Dockerfile   python runtime (pip, collectstatic, gunicorn)
docker-compose.yml   web + postgres:16-alpine + redis:7-alpine
```

## Testing

```bash
python manage.py test            # full suite (accounts, books, userpage)
python manage.py test accounts   # login, throttling, logout, checkout hCaptcha
```

> Note: the suite targets Python 3.12 (the project's runtime). On Python 3.14, four render-based tests trip over a Django 5.1 test-client incompatibility unrelated to app code.

## Roadmap

- [ ] Online payments (eSewa/Khalti) when the business is ready
- [ ] Visual restyle (Tailwind) and richer storefront interactivity
- [ ] Order emails/SMS notifications, sales reports, search
- [ ] Production hardening: `CSRF_TRUSTED_ORIGINS`, structured logging, backups

## License

Proprietary — all rights reserved. Contact the maintainer for licensing.
