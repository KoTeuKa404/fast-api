import os
import time
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery = Celery("site", broker=BROKER_URL, backend=RESULT_URL)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Kyiv",
    enable_utc=True,
    result_expires=int(os.getenv("RESULT_EXPIRES", "86400")),
    task_acks_late=True,
    task_acks_on_failure_or_timeout=True,
    worker_prefetch_multiplier=1,
    task_time_limit=600,
    task_soft_time_limit=570,
)


@celery.task(bind=True)
def fake_heavy_task(self, seconds: int = 10, steps: int = 10):
    for i in range(steps):
        time.sleep(max(0.01, seconds / steps))
        self.update_state(state="PROGRESS", meta={"current": i + 1, "total": steps})
    return {"status": "done", "processed": steps}
