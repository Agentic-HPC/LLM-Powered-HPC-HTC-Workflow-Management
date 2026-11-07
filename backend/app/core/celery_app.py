"""
Real Celery application, backed by Redis as both broker and result store.

This replaces the FastAPI `BackgroundTasks` job runner the project shipped
with originally (which only works within a single running process and is
lost on restart / doesn't scale past one machine). Celery workers are
separate OS processes - `celery -A app.core.celery_app worker` - that can
run on the same machine or be scaled out to additional worker machines,
which is the standard "job queue" pattern used in real HPC/HTC-adjacent
data platforms (Slurm/HTCondor solve the same problem at the cluster-
scheduler level; Celery solves it at the application level).

JOB_QUEUE_BACKEND controls which runner app/services/workflow_service.py
uses:
  - "celery" (recommended, requires `celery -A app.core.celery_app worker`
    running and REDIS_URL reachable)
  - "background_tasks" (fallback used automatically by tests / when Redis
    isn't available, so the app still runs without extra infrastructure)
"""
try:
    from celery import Celery

    from app.core.config import settings

    celery_app = Celery(
        "hpc_htc_ai_platform",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["app.services.workflow_service"],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_prefetch_multiplier=1,
    )

    celery_app.autodiscover_tasks(["app.services"])
except ImportError:
    class DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(f):
                f.delay = lambda *a, **k: None
                return f
            return decorator

        def autodiscover_tasks(self, *a, **k):
            pass

    celery_app = DummyCelery()
