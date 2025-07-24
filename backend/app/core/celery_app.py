# /Users/cameronwong/coinfrs_v2/backend/app/core/celery_app.py
from celery import Celery

# In a real application, the broker and backend URLs would come from a config file
# that reads environment variables.
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

celery = Celery(
    "coinfrs_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.services.ingestion.binance"]  # Add other tasks here
)

celery.conf.update(
    task_track_started=True,
)
