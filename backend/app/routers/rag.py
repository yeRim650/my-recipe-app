from fastapi import APIRouter, Depends
from typing import List
from sqlmodel import Session

from app.db import get_session

router = APIRouter()

@router.post("/recommend")
def recommend(ingredients: List[str], session: Session = Depends(get_session)):
    # TODO: RAG 로직 연결
    return {"recommendations": ["레시피 A", "레시피 B"]}
