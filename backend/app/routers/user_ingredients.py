import logging
import os
import re
from typing import List, Tuple, Pattern
from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db import get_session, engine
from app.models import (
    User,
    UserIngredient,
    IngredientMaster,
    IngredientRecipeMapping,
    Recipe,
    Instruction,
    UserRecipe,
)
from app.schemas import UserIngredientCreate, UserIngredientRead
from recipe_rag_pipeline import embed_new_recipes

router = APIRouter(
    prefix="/api/user_ingredients",
    tags=["user_ingredients"],
)

API_KEY = os.getenv("FOOD_SAFETY_API_KEY")
SERVICE_ID = os.getenv("FOOD_SAFETY_SERVICE_ID")


_ALLOWED_CHARS = re.compile(r"[^가-힣A-Za-z0-9\s]")  # 특수문자 제거용

def get_or_create_ingredient(db: Session, name: str) -> IngredientMaster:
    """
    IngredientMaster에서 name으로 조회 후 없으면 생성
    """
    ingredient = db.exec(
        select(IngredientMaster).where(IngredientMaster.name == name)
    ).first()
    if not ingredient:
        ingredient = IngredientMaster(name=name)
        db.add(ingredient)
        db.commit()
        db.refresh(ingredient)
    return ingredient

def parse_parts_dtls(text: str) -> List[Tuple[str, float, str]]:
    """
    주어진 텍스트에서 쉼표/줄바꿈으로 분할한 후:
    - ':'가 있으면 ':' 뒤 텍스트만 사용
    - 괄호 전체 제거
    - 수량(숫자)이 포함되지 않은 항목은 무시
    - 수량/단위 제거 후 재료명만 추출
    """
    parts = re.split(r"[\n,]", text)
    result = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # ":"가 있다면 뒷부분만 사용
        if ":" in part:
            part = part.split(":", 1)[-1].strip()

        # 괄호 전체 제거
        part = re.sub(r"\([^)]*\)", "", part).strip()

        # 수량이 없으면 스킵 (숫자가 포함되지 않은 경우)
        if not re.search(r"\d", part):
            continue

        # 한글과 공백만 남김
        name_only = re.sub(r"[^가-힣\s]", "", part).strip()

        if name_only:
            result.append((name_only, 0.0, ""))

    return result

@router.post(
    "/",
    response_model=UserIngredientRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user_ingredient(
    data: UserIngredientCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    # 0) user 검증
    if not session.get(User, data.user_id):
        raise HTTPException(status_code=404, detail=f"User id={data.user_id} not found")

    # 1) IngredientMaster 조회 혹은 생성
    im = get_or_create_ingredient(session, data.name)

    # 2) UserIngredient 중복 검사
    exists = session.exec(
        select(UserIngredient)
        .where(UserIngredient.user_id == data.user_id)
        .where(UserIngredient.ingredient_id == im.id)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Ingredient already exists for this user")

    # 3) UserIngredient 삽입
    ui = UserIngredient(
        user_id=data.user_id,
        ingredient_id=im.id,
        quantity=data.quantity,
    )
    session.add(ui)
    session.commit()
    session.refresh(ui)

    # 4) 백그라운드 태스크로 Recipe/Ingredient 삽입 및 임베딩
    background_tasks.add_task(process_new_ingredient, data.user_id, data.name)

    return UserIngredientRead(
        user_id=ui.user_id,
        name=data.name,
        quantity=ui.quantity,
        created_at=ui.created_at,
    )

def process_new_ingredient(user_id: int, name: str):
    logger = logging.getLogger("user_ingredients")
    logger.info(f"[BG] 시작: user_id={user_id}, name={name}")
    try:
        # 1) 외부 API 호출
        data_url = (
            f"http://openapi.foodsafetykorea.go.kr/api/"
            f"{API_KEY}/{SERVICE_ID}/json/1/100"
            f"/RCP_PARTS_DTLS={quote(name)}"
        )
        with httpx.Client(timeout=10, trust_env=True) as client:
            resp = client.get(data_url)

        logger.info(f"[BG] Data API URL   : {data_url}")
        logger.info(f"[BG] Data API Status: {resp.status_code}")
        if resp.status_code != 200 or not resp.text.strip():
            logger.error(f"[BG] Data API 응답 이상: {resp.status_code}")
            return

        data_json = resp.json()
        section = data_json.get(SERVICE_ID, {}) or {}
        items = section.get("row", []) or []
        logger.info(f"[BG] '{name}' 조회된 아이템 수: {len(items)}")

        # 2) DB 처리
        new_recipe_ids: List[int] = []
        with Session(engine) as db:
            im = get_or_create_ingredient(db, name)

            for item in items:
                title = item.get("RCP_NM") or item.get("PRDLST_NM")
                recipe_hash = title

                # 2-1) Recipe 중복 체크 / 신규 생성
                recipe = db.exec(
                    select(Recipe).where(Recipe.recipe_hash == recipe_hash)
                ).first()
                is_new = False
                if not recipe:
                    recipe = Recipe(
                        name=title,
                        category=item.get("RCP_PAT2") or item.get("PRDLST_DCNM"),
                        method=item.get("RCP_WAY2"),
                        description=item.get("RCP_PARTS_DTLS") or item.get("PIC_URL", ""),
                        calories=item.get("INFO_ENG") or item.get("NUTR_CONT1"),
                        protein=item.get("INFO_PRO") or item.get("NUTR_CONT2"),
                        carbs=item.get("INFO_CAR") or item.get("NUTR_CONT3"),
                        fat=item.get("INFO_FAT") or item.get("NUTR_CONT4"),
                        sodium=item.get("INFO_NA") or item.get("NUTR_CONT5"),
                        recipe_hash=recipe_hash,
                    )
                    db.add(recipe)
                    db.commit()
                    db.refresh(recipe)
                    is_new = True

                # 2-2) 신규 레시피인 경우 매핑
                if is_new:
                    new_recipe_ids.append(recipe.id)
                    parts = parse_parts_dtls(item.get("RCP_PARTS_DTLS", ""))
                    for ing_name, _, _ in parts:
                        pm = get_or_create_ingredient(db, ing_name)
                        exists_map = db.exec(
                            select(IngredientRecipeMapping).where(
                                IngredientRecipeMapping.recipe_id == recipe.id,
                                IngredientRecipeMapping.ingredient_id == pm.id
                            )
                        ).first()
                        if not exists_map:
                            db.add(IngredientRecipeMapping(
                                recipe_id=recipe.id,
                                ingredient_id=pm.id,
                            ))

                # 2-3) Instruction 저장
                blank_count = 0
                for i in range(1, 21):
                    key = f"MANUAL{i:02d}"
                    text = (item.get(key) or "").strip()
                    if text:
                        blank_count = 0
                        inst_exists = db.exec(
                            select(Instruction).where(
                                Instruction.recipe_id == recipe.id,
                                Instruction.step == i
                            )
                        ).first()
                        if not inst_exists:
                            db.add(Instruction(
                                recipe_id=recipe.id,
                                step=i,
                                instruction=text
                            ))
                    else:
                        blank_count += 1
                        if blank_count >= 2:
                            break

                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()

                # 2-5) UserRecipe 연결
                ur = db.exec(
                    select(UserRecipe).where(
                        UserRecipe.user_id == user_id,
                        UserRecipe.recipe_id == recipe.id
                    )
                ).first()
                if not ur:
                    db.add(UserRecipe(user_id=user_id, recipe_id=recipe.id))
                    try:
                        db.commit()
                    except IntegrityError:
                        db.rollback()

        # 3) 임베딩
        if new_recipe_ids:
            try:
                embed_new_recipes()
                logger.info(f"[BG] embed_new_recipes() 호출 완료: recipe_ids={new_recipe_ids}")
            except Exception:
                logger.exception("[BG] embed_new_recipes() 호출 중 예외 발생")

        logger.info(f"[BG] 완료: user_id={user_id}, name={name}")
    except Exception:
        logger.exception("❌ process_new_ingredient 예외 발생")

@router.get(
    "/{user_id}",
    response_model=List[UserIngredientRead],
    status_code=status.HTTP_200_OK,
)
def read_user_ingredients(
    user_id: int,
    session: Session = Depends(get_session),
):
    # 1) user 존재 확인
    if not session.get(User, user_id):
        raise HTTPException(status_code=404, detail=f"User id={user_id} not found")

    # 2) UserIngredient 조회
    ui_list = session.exec(
        select(UserIngredient).where(UserIngredient.user_id == user_id)
    ).all()

    # 3) IngredientMaster.name 과 함께 read 스키마로 반환
    return [
        UserIngredientRead(
            user_id=ui.user_id,
            name=session.get(IngredientMaster, ui.ingredient_id).name,
            quantity=ui.quantity,
            created_at=ui.created_at,
        )
        for ui in ui_list
    ]


@router.delete(
    "/{user_id}/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_ingredient(
    user_id: int,
    name: str,
    session: Session = Depends(get_session),
):
    # 1) user 존재 확인
    if not session.get(User, user_id):
        raise HTTPException(status_code=404, detail=f"User id={user_id} not found")

    # 2) IngredientMaster 조회
    im = session.exec(
        select(IngredientMaster).where(IngredientMaster.name == name)
    ).first()
    if not im:
        raise HTTPException(status_code=404, detail=f"Ingredient '{name}' not found")

    # 3) UserIngredient 조회
    ui = session.exec(
        select(UserIngredient)
        .where(UserIngredient.user_id == user_id)
        .where(UserIngredient.ingredient_id == im.id)
    ).first()
    if not ui:
        raise HTTPException(
            status_code=404,
            detail=f"Ingredient '{name}' not in user {user_id}'s fridge"
        )

    # 4) 삭제
    session.delete(ui)
    session.commit()
    return