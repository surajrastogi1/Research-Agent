from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Research, User
from app.schemas.research import ResearchCreate, ResearchResponse

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("/", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
def create_research(
    research_in: ResearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new research request for the authenticated user.
    Status starts as 'pending' until the AI agent processes it in Phase 7.
    """
    new_research = Research(
        user_id=current_user.id,
        question=research_in.question,
        status="pending",
    )
    db.add(new_research)
    db.commit()
    db.refresh(new_research)
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