from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlmodel import Session, select

from app.db import get_session
from app.models import User

router = APIRouter()

@router.post("/", response_model=User)
def create_user(user: User, session: Session = Depends(get_session)):
    # 중복 검사 예시
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.get("/", response_model=List[User])
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()
