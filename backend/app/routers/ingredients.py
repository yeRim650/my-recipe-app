from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session, select

from app.db import get_session
from app.models import Ingredient

router = APIRouter(
    prefix="/api/ingredients",
    tags=["ingredients"],
)

@router.post(
    "/",
    response_model=Ingredient,
    status_code=status.HTTP_201_CREATED,
)
def create_ingredient(ing: Ingredient, session: Session = Depends(get_session)):
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return ing

@router.get(
    "/",
    response_model=List[Ingredient],
)
def list_ingredients(session: Session = Depends(get_session)):
    return session.exec(select(Ingredient)).all()

