# MonExperience — Claude Code Instructions

## Project Overview

**MonExperience** is a Django 5.x web application backed by PostgreSQL, designed for submitting and browsing user experiences/reviews. The architecture emphasizes security, scalability, and clean separation of concerns.

---

## Tech Stack Summary

| Layer | Technology | Key Constraint |
|---|---|---|
| Backend | Django 5.x | Services & Selectors pattern |
| Database | PostgreSQL | UUID primary keys everywhere |
| Forms | Crispy Forms | FormHelper for all layouts |
| Storage | Local filesystem | `MEDIA_ROOT` → `uploads/` folder |
| Security | Bleach + django-ratelimit | Sanitize all text, rate-limit submissions |
| Tasks | Celery + Redis | Background image processing & emails |

---

## Coding Conventions

### 1. Services & Selectors Pattern
Keep views thin. All business logic lives in `services.py` and `selectors.py` within each Django app.

```
app/
  views.py        # HTTP only — call services/selectors, return responses
  services.py     # Write operations (create, update, delete)
  selectors.py    # Read operations (queries, filters)
  models.py       # Data shape only, minimal methods
```

**Example:**
```python
# views.py
def review_create_view(request):
    form = ReviewForm(request.POST)
    if form.is_valid():
        review_create(user=request.user, data=form.cleaned_data)  # service call
        return redirect("review_list")
    return render(request, "reviews/create.html", {"form": form})
```

### 2. UUID Primary Keys
All models must use UUIDs as primary keys. No integer auto-increment IDs.

```python
import uuid
from django.db import models

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

### 3. Crispy Forms with FormHelper
All forms must use `FormHelper` for layout — no manual HTML form rendering.

```python
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class ReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("title"), Column("rating")),
            "body",
            Submit("submit", "Submit Review"),
        )
```

### 4. Local File Storage
Use Django's default file storage. Media files are stored in the `uploads/` folder inside `MEDIA_ROOT`. Static files are served from `STATIC_ROOT`.

```python
# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "uploads"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

```python
# config/urls.py — serve media in development
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Upload fields on models should use `upload_to` sub-folders to keep files organized:

```python
class Review(BaseModel):
    evidence = models.FileField(upload_to="reviews/evidence/", blank=True)
    thumbnail = models.ImageField(upload_to="reviews/thumbnails/", blank=True)
```

### 5. Security: Bleach + Rate Limiting

**Sanitize all review text before saving:**
```python
import bleach

ALLOWED_TAGS = ["b", "i", "em", "strong", "p", "ul", "ol", "li"]

def sanitize_review_body(raw_html: str) -> str:
    return bleach.clean(raw_html, tags=ALLOWED_TAGS, strip=True)
```

**Rate-limit anonymous submissions:**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key="ip", rate="5/h", method="POST", block=True)
def review_create_view(request):
    ...
```

### 6. Celery + Redis for Background Tasks
Never process images or send emails synchronously in a view. Always offload to Celery.

```python
# tasks.py
from celery import shared_task

@shared_task
def process_review_images(review_id: str):
    # image resizing, thumbnail generation, etc.
    ...

@shared_task
def send_review_confirmation_email(user_id: str, review_id: str):
    ...
```

```python
# services.py — after creating a review, enqueue tasks
def review_create(user, data):
    review = Review.objects.create(user=user, **data)
    process_review_images.delay(str(review.id))
    send_review_confirmation_email.delay(str(user.id), str(review.id))
    return review
```

---

## Project Structure

```
monexperience/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── apps/
│   ├── common/           # BaseModel, shared utilities
│   ├── users/            # Auth, profiles
│   └── reviews/          # Core review app
│       ├── models.py
│       ├── views.py
│       ├── services.py
│       ├── selectors.py
│       ├── forms.py
│       ├── tasks.py
│       └── urls.py
├── templates/
├── static/
└── requirements/
    ├── base.txt
    └── production.txt
```

---

## Key Dependencies

```
# requirements/base.txt
Django>=5.0
psycopg[binary]
django-crispy-forms
crispy-bootstrap5
bleach
django-ratelimit
celery
redis
django-environ
Pillow
```

---

## Environment Variables

```env
SECRET_KEY=...
DEBUG=False
DATABASE_URL=postgres://user:pass@host:5432/monexperience
REDIS_URL=redis://localhost:6379/0
MEDIA_ROOT=/path/to/uploads
```

---

## Claude Code Instructions

When implementing features, follow this checklist:

1. **Models** — inherit from `BaseModel` (UUID pk). Add indexes for frequently filtered fields.
2. **Business logic** — write to `services.py` (writes) or `selectors.py` (reads). Never put queries directly in views.
3. **Views** — thin. Validate with a form, call a service, redirect or render.
4. **Forms** — always configure `FormHelper` with an explicit `Layout`.
5. **Text inputs** — pass through `bleach.clean()` inside the service before saving.
6. **Anonymous POST endpoints** — apply `@ratelimit` decorator.
7. **File uploads** — store under `MEDIA_ROOT/uploads/` using `upload_to` sub-folders per model. Serve via `MEDIA_URL` in development; use a proper web server (nginx) in production to serve the `uploads/` directory.
8. **Async work** — any image processing or email sending must go through a `@shared_task`.
9. **Tests** — write a service-level test and a view-level integration test for every new feature.
10. **Migrations** — always run `makemigrations` and review the generated file before applying.

---

## Example: End-to-End Review Submission Flow

```
User POST /reviews/new/
  → view validates ReviewForm
  → calls review_create(user, data)
      → sanitize body with bleach
      → Review.objects.create(...)
      → process_review_images.delay(review.id)   [Celery]
      → send_review_confirmation_email.delay(...) [Celery]
  → redirect to /reviews/<uuid>/
  → template renders file URL via review.evidence.url (served from /media/uploads/)
```

---

*This document is the authoritative reference for Claude Code when building MonExperience. Follow all conventions above before writing any code.*
