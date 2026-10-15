import os
from celery import Celery

# Read env (worker runs as separate process, so no FastAPI loads .env)
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL is not set in .env")

celery_app = Celery(
    "research_agent",
    broker=REDIS_URL,           # where tasks are queued
    backend=REDIS_URL,          # where task results are stored
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,    # lets us query "is this task running?"
    task_time_limit=600,        # hard kill after 10 min
    task_soft_time_limit=540,   # soft limit — task can catch and clean up
)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=10)
def process_research_task(self, research_id: str, question: str):
    """
    Celery task — runs in a separate worker process.
    Opens its own DB session (same rule as BackgroundTasks).
    """
    from app.services.research_service import run_research_pipeline
    from app.db.session import SessionLocal
    from app.models.models import Research, Source
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        research = db.query(Research).filter(Research.id == research_id).first()
        if not research:
            return  # deleted before worker picked it up

        research.status = "processing"
        db.commit()

        result = run_research_pipeline(question)

        for src in result["sources"]:
            db.add(Source(
                research_id=research.id,
                title=src["title"],
                url=src["url"],
                content=src["content"],
            ))

        research.report = result["report"]
        research.status = "completed"
        research.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        db.rollback()
        research = db.query(Research).filter(Research.id == research_id).first()
        if research:
            # If we have retries left, leave it as "processing" and retry
            if self.request.retries < self.max_retries:
                research.status = "processing"
                db.commit()
                raise self.retry(exc=exc)
            else:
                research.status = "failed"
                db.commit()
        raise

    finally:
        db.close()