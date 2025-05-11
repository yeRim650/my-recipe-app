from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session, select

from app.db import get_session
from app.models import UserIngredient
from app.schemas import UserIngredientCreate, UserIngredientRead

router = APIRouter(
    prefix="/api/user_ingredients",
    tags=["user_ingredients"],
)

@router.post(
    "/",
    response_model=UserIngredientRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user_ingredient(
    data: UserIngredientCreate,
    session: Session = Depends(get_session),
):
    # (user_id, name) 중복 검사
    exists = session.exec(
        select(UserIngredient)
        .where(UserIngredient.user_id == data.user_id)
        .where(UserIngredient.name    == data.name)
    ).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ingredient already exists for this user",
        )

    ui = UserIngredient(**data.dict())
    session.add(ui)
    session.commit()
    session.refresh(ui)
    return ui


@router.get(
    "/",
    response_model=List[UserIngredientRead],
)
def list_user_ingredients(session: Session = Depends(get_session)):
    return session.exec(select(UserIngredient)).all()


@router.get(
    "/{user_id}/{name}",
    response_model=UserIngredientRead,
)
def get_user_ingredient(
    user_id: int,
    name:    str,
    session: Session = Depends(get_session),
):
    ui = session.get(UserIngredient, (user_id, name))
    if not ui:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User ingredient not found",
        )
    return ui


@router.put(
    "/{user_id}/{name}",
    response_model=UserIngredientRead,
)
def update_user_ingredient(
    user_id: int,
    name:    str,
    data:    UserIngredientCreate,
    session: Session = Depends(get_session),
):
    ui = session.get(UserIngredient, (user_id, name))
    if not ui:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User ingredient not found",
        )

    # 수량 업데이트
    ui.quantity = data.quantity

    session.add(ui)
    session.commit()
    session.refresh(ui)
    return ui


@router.delete(
    "/{user_id}/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_ingredient(
    user_id: int,
    name:    str,
    session: Session = Depends(get_session),
):
    ui = session.get(UserIngredient, (user_id, name))
    if not ui:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User ingredient not found",
        )
    session.delete(ui)
    session.commit()
    return
