# app/api/rag.py

import re
import json
import os

import openai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from sqlmodel import Session, select

from app.db import get_session
from app.models import Recipe, IngredientMaster, UserIngredient
from recipe_rag_pipeline import recommend_for_user

# OpenAI 클라이언트 초기화
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RecommendRequest(BaseModel):
    user_id: int
    query: str
    top_k: Optional[int] = 5
    boost: Optional[float] = 0.2


def extract_ingredient_names(text: str) -> str:
    parts = re.split(r"[\n,]", text)
    ingredients = []
    for part in parts:
        cleaned = re.sub(
            r"\s*\d+(?:\.\d+)?\s*[^\s()]*\s*(?:\([^)]*\))?",
            "",
            part
        ).strip()
        if cleaned:
            ingredients.append(cleaned)
    return ", ".join(ingredients)


def generate_llm_recommendations(
    query: str,
    user_ingredients: List[str],
    recipes: List[str],
    model: str = "gpt-3.5-turbo"
) -> List[str]:
    """
    query: 사용자 요청 문장
    user_ingredients: 사용자가 명시한 재료 리스트
    recipes: 후보 레시피 목록 (각 dict에 'id','name','method','category','description' 포함)
    model: "gpt-3.5-turbo" 사용
    """
    # 1) 후보 레시피 목록 문자열화
    recipe_lines = "\n".join(
        f"- {r['id']} / {r['name']} ({r['method']} / {r['category']}) — 재료: {r['description']}"
        for r in recipes
    )

    # 2) 프롬프트 작성
    prompt = f"""
[사용자 요청] "{query}"

[후보 레시피] (ID / 이름 / method / category / 재료):
{recipe_lines}

RULES:
1. 사용자 요청과 완전히 맞지 않는 레시피는 전부 제거.
2. 특정 재료가 명시된 경우, 주어진 재료(description) 목록만 보고 일치하는 레시피만 선택.
3. 요청에 조리법·분류 단서가 있으면 그 조건을 반드시 충족하는 레시피만 선택.
4. reason에는 주어진 재료 외 다른 재료명을 절대 넣지 말 것. 읽는 사용자의 입맛이 확 당길 만큼 생생하게 서술하되, **공백 포함 한글 기준 최소 40자 아허**로 추천 이유 작성
5. 후보 순서를 유지하며 조건을 만족하는 상위 3개 선택(모자라면 가능한 만큼).

다시 강조: JSON 배열(id(int), name(str), reason(str)) 외에는 아무것도 출력하지 마세요.
"""

    # 3) OpenAI API 호출 (새 openai-python v1.x 인터페이스)
    resp = openai.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 요리 추천 도우미입니다. 반드시 순수 JSON 배열만 반환하세요. "
                    "배열 길이는 0~3, 필드는 id(int)/name(str)/reason(str)뿐입니다."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )

    # 4) 결과 문자열 정제
    raw = resp.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    # 5) JSON 파싱 및 검증
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError(f"LLM 응답이 JSON 배열이 아닙니다:\n{raw}")
    return data


@router.post("/recommend")
def recommend(req: RecommendRequest, session: Session = Depends(get_session)):
    try:
        # 1) RAG로 후보 레시피 조회
        recipes: List[Recipe] = recommend_for_user(
            user_id=req.user_id,
            query=req.query,
            top_k=req.top_k,
            boost=req.boost
        )

        # 2) 사용자 냉장고 재료 조회
        fridge = [
            name for name in session.exec(
                select(IngredientMaster.name)
                .join(UserIngredient, IngredientMaster.id == UserIngredient.ingredient_id)
                .where(UserIngredient.user_id == req.user_id)
            )
        ]

        # 3) LLM 입력용 단순화 (최대 20개)
        simplified = [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category or "",
                "method": r.method or "",
                "description": extract_ingredient_names(r.description or "")
            }
            for r in recipes
        ]

        # 4) LLM 호출 (id, name, reason 포함)
        llm_recs = generate_llm_recommendations(
            query=req.query,
            user_ingredients=fridge,
            recipes=simplified[:20]
        )

        # 5) LLM 응답의 id 로 실제 Recipe 레코드 조회
        rec_ids = [rec["id"] for rec in llm_recs]
        db_recipes = {
            r.id: r for r in session.exec(
                select(Recipe).where(Recipe.id.in_(rec_ids))
            ).all()
        }

        # 6) 최종 응답 포맷으로 통합
        final_recs = []
        for rec in llm_recs:
            recipe = db_recipes.get(rec["id"])
            if not recipe:
                continue
            final_recs.append({
                "id":          recipe.id,
                "name":        recipe.name,
                "category":    recipe.category,
                "method":      recipe.method,
                "description": recipe.description,
                "reason":      rec["reason"],
            })

        return {"fridge": fridge, "recommendations": final_recs}

    except ValueError as ve:
        raise HTTPException(status_code=500, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"추천 중 오류 발생: {e}")
