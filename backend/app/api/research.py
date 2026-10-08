from typing import List
from uuid import UUID
from datetime import datetime,timezone
from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import logging
import json


from app.api.deps import get_current_user
from app.db.session import get_db, SessionLocal
from app.models.models import Research, User, Source
from app.schemas.research import ResearchCreate, ResearchResponse
from app.services.research_service import run_research_pipeline
from app.services.research_service import process_research
from app.services.research_service import process_research, stream_research_pipeline

router = APIRouter(prefix="/research", tags=["Research"])


logger = logging.getLogger(__name__)
@router.post("/", response_model=ResearchResponse, status_code=status.HTTP_202_ACCEPTED)
def create_research(
    research_in: ResearchCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Create the row immediately — client gets an ID right now
    new_research = Research(
        user_id=current_user.id,
        question=research_in.question,
        status="pending",
    )
    db.add(new_research)
    db.commit()
    db.refresh(new_research)

    # 2. Schedule the agent to run AFTER the response is sent
    background_tasks.add_task(
        process_research,
        str(new_research.id),
        research_in.question,
    )

    # 3. Return 202 immediately with the pending job
    return new_research

@router.get("/", response_model=List[ResearchResponse])
def get_user_researches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves all research reports submitted by the logged-in user.
    """
    researches = (
        db.query(Research)
        .filter(Research.user_id == current_user.id)
        .order_by(Research.created_at.desc())
        .all()
    )
    return researches


@router.get("/{research_id}", response_model=ResearchResponse)
def get_research_by_id(
    research_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a specific research report by ID. 
    Ensures users can only access their own research.
    """
    research = (
        db.query(Research)
        .filter(Research.id == research_id, Research.user_id == current_user.id)
        .first()
    )
    if not research:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found or unauthorized access",
        )
    return research

def _sse(event: str, data: dict) -> str:
    """Format a dict as an SSE frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/stream")
def stream_research(
    research_in: ResearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Same pipeline, but streamed live as SSE.
    The HTTP response stays open and pushes events until the report is done.
    """
    # 1. Create the DB row FIRST so the client has an ID even if streaming dies
    new_research = Research(
        user_id=current_user.id,
        question=research_in.question,
        status="processing",
    )
    db.add(new_research)
    db.commit()
    db.refresh(new_research)

    # Capture what we need as plain values — the generator runs AFTER this function returns,
    # so the request's `db` session will be closed by then.
    research_id = str(new_research.id)
    question = research_in.question

    def event_generator():
        # Own session, exactly like the background task
        session = SessionLocal()
        try:
            # Tell the client its research ID right away
            yield _sse("research_id", {"id": research_id})

            full_report = ""
            sources_data = []

            for event in stream_research_pipeline(question):
                name = event["event"]
                data = event["data"]

                if name == "sources":
                    sources_data = data
                elif name == "done":
                    full_report = data["report"]

                # Forward the event to the client
                yield _sse(name, data)

            # ---- Persist everything now that the stream is done ----
            research = session.query(Research).filter(Research.id == research_id).first()
            if research is None:
                return

            for src in sources_data:
                session.add(Source(
                    research_id=research_id,
                    title=src["title"],
                    url=src["url"],
                    content=src["content"],
                ))

            research.report = full_report
            research.status = "completed"
            research.completed_at = datetime.now(timezone.utc)
            session.commit()

        except Exception as e:
            session.rollback()
            research = session.query(Research).filter(Research.id == research_id).first()
            if research:
                research.status = "failed"
                session.commit()
            yield _sse("error", {"message": str(e)})
        finally:
            session.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # tell nginx/proxies not to buffer
        },
    )