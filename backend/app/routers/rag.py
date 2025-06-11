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
    recipes: List[dict],
    model: str = "gpt-3.5-turbo"
) -> List[dict]:
    # 각 레시피 앞에 ID를 포함해서 나열
    recipe_lines = "\n".join(
        f"- {r['id']} / {r['name']} ({r['method']} / {r['category']}) — 재료: {r['description']}"
        for r in recipes
    )

    prompt = f"""
사용자 요청(최우선): "{query}"

후보 레시피 (ID / 이름 / 조리법 / 분류 / 재료-단순설명):
{recipe_lines}

1) 20개의 레시피 중, 사용자 요청을 완벽히 부합하지 않는 레시피는 전부 제거하세요.
2) 사용자 요청과 동일한 레시피 명이 있으면 추천하세요.
3) 남은 레시피 중, 사용자 요청을 완벽히 부합하지 않는 레시피는 한번 더 제거하세요.
4) **반드시 추천 3개을 뽑을 때 사용자 요청에 맞는 조리법(method)과 분류(category)로 추천**하세요. 만약 분류가 일품인 경우는 이름을 보고 판단하세요.
5) 추천 이유(reason)는 사용자 요청에 100% 부합하도록 작성하며, 레시피에 없는 재료가 절대 포함되지 않게 주의하고, 읽는 사용자의 입맛이 확 당길 만큼 생생하게 서술하되, **공백 포함 한글 기준 최소 40자 이상**으로 작성하세요.
6) 후보 레시피 순서를 유지하며, 위 조건을 만족하는 상위 3개 선택 
7) JSON 배열(id, name, reason) 3개로 반환

예시:
```json
[
  {{ "id": 42, "name": "오징어볶음", "reason": "탱글탱글한 문어가…" }},
  {{ "id": 105, "name": "장어수육구이", "reason": "부드러운 장어살이…" }},
  {{ "id": 87, "name": "문어핫바", "reason": "쫄깃한 문어와…" }}
]
```"""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "당신은 요리 추천 도우미입니다. 사용자의 요청과 다른 레시피는 절대 추천하지 않습니다."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    text = resp.choices[0].message.content

    # ``` 코드 블록 제거
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM 응답(JSON) 파싱 실패: {e}\n\n정제 전:\n{text}\n\n정제 후:\n{cleaned}"
        )


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
