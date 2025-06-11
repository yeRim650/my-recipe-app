# app/routers/rag.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_session
from recipe_rag_pipeline import recommend_for_user
from app.models import Recipe
from sqlmodel import Session

router = APIRouter(
    prefix="/api/rag",
    tags=["rag"],
)

class RecommendRequest(BaseModel):
    user_id: int
    query: str
    top_k: Optional[int] = 5
    boost: Optional[float] = 0.2

@router.post("/recommend")
def recommend(req: RecommendRequest, session: Session = Depends(get_session)):
    """
    사용자 ID와 검색 쿼리를 받아, recipe_rag_pipeline.recommend_for_user를 통해 레시피를 추천합니다.
    - req.user_id: 추천을 요청한 사용자 ID
    - req.query: 검색 쿼리 (예: "면 요리")
    - req.top_k: 상위 몇 개를 추천할지 (기본 5)
    - req.boost: 냉장고 재료 매칭 가중치 (기본 0.2)
    """
    try:
        recipes: List[Recipe] = recommend_for_user(
            user_id=req.user_id,
            query=req.query,
            top_k=req.top_k,
            boost=req.boost
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"추천 중 오류 발생: {e}")

    result = []
    for r in recipes:
        result.append({
            "id": r.id,
            "name": r.name,
            "category": r.category,
            "method": r.method,
            # 필요하다면 추가 필드 삽입
        })

    return {"recommendations": result}
