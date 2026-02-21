# MonExperience

A Django 5.x web application for submitting and browsing user experiences/reviews.

## Tech Stack

- Backend: Django 5.x with PostgreSQL
- Forms: Crispy Forms with Bootstrap5
- Storage: Local filesystem (MEDIA_ROOT → uploads/)
- Security: Bleach + django-ratelimit
- Tasks: Celery + Redis

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements/base.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Start development server:
```bash
python manage.py runserver
```

## Project Structure

```
monexperience/
├── config/          # Django settings, URLs, Celery
├── apps/            # Django applications
├── templates/       # Base templates
├── static/          # Static files
├── uploads/         # Media files (created at runtime)
└── requirements/   # Dependency files
```
