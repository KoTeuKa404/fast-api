import os, time
from celery import Celery

celery = Celery(
    "fastapi",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_RESULT_URL", "redis://redis:6379/1"),
)

@celery.task(bind=True)
def fake_heavy_task(self, seconds: int = 8, steps: int = 8):
    for i in range(steps):
        time.sleep(max(0.01, seconds/steps))
        self.update_state(state="PROGRESS", meta={"current": i+1, "total": steps})
    return {"status": "done", "processed": steps}
