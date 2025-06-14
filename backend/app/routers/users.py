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
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    session: Session = Depends(get_session),
):
    existing = session.exec(
        select(User).where(User.email == data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(**data.dict())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post(
    "/login",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def login_user(
    data: UserCreate,
    session: Session = Depends(get_session),
):
    """
    로그인: username과 email이 모두 일치하는 사용자가 있으면 반환.
    """
    user = session.exec(
        select(User).where(
            User.username == data.username,
            User.email == data.email,
        )
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or email",
        )
    return user


@router.get(
    "/",
    response_model=List[UserRead],
)
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@router.get(
    "/{user_id}",
    response_model=UserRead,
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
    response_model=UserRead,
)
def update_user(
    user_id: int,
    data: UserCreate,
    session: Session = Depends(get_session),
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

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
    db_user.email = data.email
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
