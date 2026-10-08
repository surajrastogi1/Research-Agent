from typing import List
from uuid import UUID
from datetime import datetime,timezone
from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from sqlalchemy.orm import Session
import logging


from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Research, User, Source
from app.schemas.research import ResearchCreate, ResearchResponse
from app.services.research_service import run_research_pipeline
from app.services.research_service import process_research

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
