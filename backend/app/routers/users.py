from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session, select

from app.db import get_session
from app.models import User
from app.schemas import UserCreate, UserRead

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)


@router.post(
    "/",
    response_model=UserRead,            # ★ 응답에는 UserRead 사용
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,                   # ★ 입력은 UserCreate 만 받음
    session: Session = Depends(get_session),
):
    # 이메일 중복 검사
    existing = session.exec(
        select(User).where(User.email == data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # User 인스턴스 생성: created_at/updated_at 은 DB가 채워줍니다
    user = User(**data.dict())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get(
    "/",
    response_model=List[UserRead],      # 리스트 응답도 UserRead
)
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@router.get(
    "/{user_id}",
    response_model=UserRead,            # 단건 조회에도 UserRead
)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserRead,            # 수정 응답도 UserRead
)
def update_user(
    user_id: int,
    data: UserCreate,                   # ★ 수정도 UserCreate
    session: Session = Depends(get_session),
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 이메일 변경 시 중복 검사
    if data.email != db_user.email:
        dup = session.exec(
            select(User).where(User.email == data.email)
        ).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    db_user.username = data.username
    db_user.email    = data.email
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    session.delete(user)
    session.commit()
    return
