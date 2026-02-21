import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("monexperience")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Suppress Redis connection errors at startup
app.conf.task_ignore_result = True
app.conf.broker_connection_retry_on_startup = False
