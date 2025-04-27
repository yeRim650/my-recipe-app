from fastapi import APIRouter, Depends
from typing import List
from sqlmodel import Session, select

from app.db import get_session
from app.models import Recipe

router = APIRouter()

@router.get("/", response_model=List[Recipe])
def list_recipes(session: Session = Depends(get_session)):
    return session.exec(select(Recipe)).all()
