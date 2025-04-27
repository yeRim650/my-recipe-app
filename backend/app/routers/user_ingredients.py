from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select

from app.db import get_session
from app.models import UserIngredient

router = APIRouter()

@router.post("/", response_model=UserIngredient)
def add_user_ingredient(ing: UserIngredient, session: Session = Depends(get_session)):
    # 간단 중복 방지
    existing = session.exec(
        select(UserIngredient)
        .where(UserIngredient.user_id == ing.user_id)
        .where(UserIngredient.name == ing.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ingredient already exists")
    session.add(ing)
    session.commit()
    session.refresh(ing)
    return ing

@router.get("/", response_model=List[UserIngredient])
def list_user_ingredients(session: Session = Depends(get_session)):
    return session.exec(select(UserIngredient)).all()
