# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MonExperience** is a Django 5.x + PostgreSQL web application for submitting and browsing user experiences/reviews. Uses phone-based authentication.

---

## Common Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements/base.txt
cp .env.example .env
python manage.py migrate

# Run development server
python manage.py runserver

# Run Celery worker (for background tasks)
celery -A config worker -l INFO

# Create migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Management commands
python manage.py populate_companies  # Seed company data
```

---

## Architecture

### Apps Structure

| App | Purpose |
|---|---|
| `apps/common` | BaseModel (UUID pk + timestamps) |
| `apps/users` | Custom User model with phone auth |
| `apps/companies` | Company directory with claim/verification system |
| `apps/reviews` | Core review system (models, views, services, selectors, forms, tasks) |

### Key Design Patterns

1. **Services & Selectors** — Business logic in `services.py` (writes) and `selectors.py` (reads). Views are thin.

2. **UUID Primary Keys** — All core models inherit from `BaseModel` which provides `id = UUIDField`. Company model uses its own UUIDField.

3. **Crispy Forms** — All forms use `FormHelper` with explicit `Layout`.

4. **Bleach + Rate Limiting** — Sanitize text inputs, rate-limit anonymous POSTs.

5. **Celery + Redis** — Background tasks for image processing and emails.

6. **Company Verification** — Companies can be claimed via `CompanyClaim` model with multiple verification methods (email, documents, employment, website).

### Data Flow

```
User POST /reviews/new/
  → view: validates ReviewForm, calls service
  → service: sanitize with bleach, create Review, enqueue tasks
  → tasks: process images, send emails (async via Celery)
  → redirect to review detail
```

---

## Key Files

- `config/settings/base.py` — Django settings
- `config/urls.py` — URL routing
- `config/celery.py` — Celery configuration
- `apps/common/models.py` — BaseModel with UUID pk
- `apps/reviews/models.py` — Review, Comment, Tag, ReviewUpdate
- `apps/reviews/services.py` — Business logic for reviews (writes)
- `apps/reviews/selectors.py` — Query logic for reviews (reads)
- `apps/companies/models.py` — Company, CompanyClaim models
- `apps/companies/services.py` — Business logic for companies
- `apps/companies/selectors.py` — Query logic for companies
- `apps/users/models.py` — Custom User with phone auth (no username)

---

## Dependencies

```
Django>=5.0, psycopg[binary], django-crispy-forms, crispy-bootstrap5,
bleach, django-ratelimit, django-countries, phonenumbers,
celery, redis, django-environ, Pillow, gunicorn
```

Production also adds: `django-redis`, `sentry-sdk`

---

## Environment Variables

```
SECRET_KEY=...
DEBUG=True/False
DATABASE_URL=postgres://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Security Requirements

- All user text input → sanitize with `bleach.clean()`
- Anonymous POST endpoints → `@ratelimit` decorator
- File uploads → use `upload_to` subfolders in `MEDIA_ROOT/uploads/`
- Image processing → always via Celery `@shared_task`

---

## Implementation Checklist

When adding features:
1. Model → inherit from `BaseModel` (UUID pk)
2. Business logic → `services.py` (writes) or `selectors.py` (reads)
3. Views → thin, validate with form, call service, redirect/render
4. Forms → use `FormHelper` with `Layout`
5. Text fields → sanitize with `bleach.clean()` in service
6. Anonymous POST → add `@ratelimit`
7. File uploads → use `upload_to="appname/"` subfolder
8. Async work → Celery `@shared_task`
9. Migrations → run `makemigrations`, review before apply
