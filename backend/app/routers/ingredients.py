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

# @router.get(
#     "/{ingredient_id}",
#     response_model=Ingredient,
# )
# def get_ingredient(ingredient_id: int, session: Session = Depends(get_session)):
#     ing = session.get(Ingredient, ingredient_id)
#     if not ing:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
#     return ing

# @router.put(
#     "/{ingredient_id}",
#     response_model=Ingredient,
# )
# def update_ingredient(
#     ingredient_id: int,
#     ing_in: Ingredient,
#     session: Session = Depends(get_session),
# ):
#     ing = session.get(Ingredient, ingredient_id)
#     if not ing:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
#     ing.name = ing_in.name
#     ing.quantity = ing_in.quantity
#     ing.unit = ing_in.unit
#     session.add(ing)
#     session.commit()
#     session.refresh(ing)
#     return ing

# @router.delete(
#     "/{ingredient_id}",
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# def delete_ingredient(ingredient_id: int, session: Session = Depends(get_session)):
#     ing = session.get(Ingredient, ingredient_id)
#     if not ing:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
#     session.delete(ing)
#     session.commit()
#     return
