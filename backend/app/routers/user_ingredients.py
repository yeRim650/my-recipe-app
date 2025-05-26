import logging
import os
import re
from typing import List, Tuple
from urllib.parse import quote
from json import JSONDecodeError

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

logger = logging.getLogger("user_ingredients")
logger.setLevel(logging.INFO)

router = APIRouter(
    prefix="/api/user_ingredients",
    tags=["user_ingredients"],
)

API_KEY    = os.getenv("FOOD_SAFETY_API_KEY")
SERVICE_ID = os.getenv("FOOD_SAFETY_SERVICE_ID")


def parse_parts_dtls(text: str) -> List[Tuple[str, float, str]]:
    """
    RCP_PARTS_DTLS 문자열에서 재료 목록을
    [(재료명, 수량(숫자), 단위 문자열), …] 형태로 파싱합니다.
    """
    lines = text.split("\n")
    if len(lines) < 2:
        return []
    parts = [p.strip() for p in lines[1].split(",") if p.strip()]

    pattern = re.compile(
        r"^(?P<name>[^\d]+?)\s+"
        r"(?P<number>\d+(?:\.\d+)?)"
        r"(?P<unit>[^\d(][^(\s]*)?"
        r"(?P<extra>\(.*\))?$"
    )
    out: List[Tuple[str, float, str]] = []
    for p in parts:
        m = pattern.match(p)
        if not m:
            continue
        name   = m.group("name").strip()
        number = float(m.group("number"))
        unit   = (m.group("unit") or "").strip()
        extra  = (m.group("extra") or "").strip()
        full_unit = f"{unit}{extra}" if extra else unit
        out.append((name, number, full_unit))
    return out


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
    im = session.exec(
        select(IngredientMaster).where(IngredientMaster.name == data.name)
    ).first()
    if not im:
        im = IngredientMaster(name=data.name)
        session.add(im)
        session.commit()
        session.refresh(im)

    # 2) UserIngredient 중복 검사
    exists = session.exec(
        select(UserIngredient)
        .where(UserIngredient.user_id       == data.user_id)
        .where(UserIngredient.ingredient_id == im.id)
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Ingredient already exists for this user")

    # 3) UserIngredient 삽입
    ui = UserIngredient(
        user_id       = data.user_id,
        ingredient_id = im.id,
        quantity      = data.quantity,
    )
    session.add(ui)
    session.commit()
    session.refresh(ui)

    # 4) 백그라운드 태스크로 Recipe/Ingredient 삽입
    background_tasks.add_task(process_new_ingredient, data.user_id, data.name)
    
    return UserIngredientRead(
        user_id    = ui.user_id,
        name       = data.name,
        quantity   = ui.quantity,
        created_at = ui.created_at,
    )


def process_new_ingredient(user_id: int, name: str):
    logger.info(f"[BG] 시작: user_id={user_id}, name={name}")
    try:
        # 1) 외부 API 호출
        data_url = (
            f"http://openapi.foodsafetykorea.go.kr/api/"
            f"{API_KEY}/{SERVICE_ID}/json/1/10"
            f"/RCP_PARTS_DTLS={quote(name)}"
        )
        with httpx.Client(timeout=10) as client:
            resp = client.get(data_url)

        # 로그 남기기
        print(f"[BG] Data API URL   : {data_url}")
        print(f"[BG] Data API Status: {resp.status_code}")
        print(f"[BG] Data API Body  : {resp.text!r}")

        if resp.status_code != 200 or not resp.text.strip():
            logger.error(f"[BG] Data API 응답 이상: {resp.status_code}")
            return

        data_json = resp.json()
        section   = data_json.get(SERVICE_ID, {}) or {}
        items     = section.get("row", []) or []
        logger.info(f"[BG] '{name}' 조회된 아이템 수: {len(items)}")

        # 2) DB 처리
        with Session(engine) as db:
            # IngredientMaster 보장
            im = db.exec(
                select(IngredientMaster).where(IngredientMaster.name == name)
            ).first()
            if not im:
                im = IngredientMaster(name=name)
                db.add(im); db.commit(); db.refresh(im)

            for item in items:
                title       = item.get("RCP_NM") or item.get("PRDLST_NM")
                recipe_hash = title

                # 2-1) Recipe 중복 체크 / 신규 생성
                recipe = db.exec(
                    select(Recipe).where(Recipe.recipe_hash == recipe_hash)
                ).first()
                is_new = False
                if not recipe:
                    recipe = Recipe(
                        name        = title,
                        category    = item.get("RCP_PAT2")  or item.get("PRDLST_DCNM"),
                        method      = item.get("RCP_WAY2"),
                        description = item.get("RCP_PARTS_DTLS") or item.get("PIC_URL",""),
                        calories    = item.get("INFO_NA")   or item.get("NUTR_CONT1"),
                        protein     = item.get("INFO_PRO")  or item.get("NUTR_CONT2"),
                        carbs       = item.get("INFO_CAR")  or item.get("NUTR_CONT3"),
                        fat         = item.get("INFO_FAT")  or item.get("NUTR_CONT4"),
                        sodium      = item.get("INFO_NA")   or item.get("NUTR_CONT5"),
                        recipe_hash = recipe_hash,
                    )
                    db.add(recipe); db.commit(); db.refresh(recipe)
                    is_new = True

                # 2-2) 신규 레시피인 경우에만 parts_dtls 파싱 후 mapping 삽입
                if is_new:
                    parts = parse_parts_dtls(item.get("RCP_PARTS_DTLS",""))
                    for ing_name, _, _ in parts:
                        pm = db.exec(
                            select(IngredientMaster).where(IngredientMaster.name == ing_name)
                        ).first()
                        if not pm:
                            pm = IngredientMaster(name=ing_name)
                            db.add(pm); db.commit(); db.refresh(pm)

                        exists_map = db.exec(
                            select(IngredientRecipeMapping)
                            .where(IngredientRecipeMapping.recipe_id     == recipe.id)
                            .where(IngredientRecipeMapping.ingredient_id == pm.id)
                        ).first()
                        if not exists_map:
                            db.add(IngredientRecipeMapping(
                                recipe_id     = recipe.id,
                                ingredient_id = pm.id,
                            ))

                # 2-3) MANUAL01~20을 step 1~20으로 저장, 빈 값이 연속 2번 나오면 중단
                blank_count = 0
                for i in range(1, 21):
                    key = f"MANUAL{i:02d}"
                    text = (item.get(key) or "").strip()
                    if text:
                        blank_count = 0
                        inst_exists = db.exec(
                            select(Instruction)
                            .where(Instruction.recipe_id == recipe.id)
                            .where(Instruction.step      == i)
                        ).first()
                        if not inst_exists:
                            db.add(Instruction(
                                recipe_id   = recipe.id,
                                step        = i,
                                instruction = text
                            ))
                    else:
                        blank_count += 1
                        if blank_count >= 2:
                            break

                # 2-4) UserRecipe 연결
                ur = db.exec(
                    select(UserRecipe)
                    .where(UserRecipe.user_id   == user_id)
                    .where(UserRecipe.recipe_id == recipe.id)
                ).first()
                if not ur:
                    db.add(UserRecipe(
                        user_id   = user_id,
                        recipe_id = recipe.id,
                    ))

                # 최종 커밋
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()

        logger.info(f"[BG] 완료: user_id={user_id}, name={name}")

    except Exception:
        logger.exception("❌ process_new_ingredient 예외 발생")


# 이하 list/get/put/delete 엔드포인트는 그대로...



@router.get(
    "/",
    response_model=List[UserIngredientRead],
)
def list_user_ingredients(session: Session = Depends(get_session)):
    stmt    = select(UserIngredient, IngredientMaster.name).join(
                  IngredientMaster,
                  UserIngredient.ingredient_id == IngredientMaster.id
              )
    results = session.exec(stmt).all()

    out: List[UserIngredientRead] = []
    for ui, nm in results:
        out.append(UserIngredientRead(
            user_id    = ui.user_id,
            name       = nm,
            quantity   = ui.quantity,
            created_at = ui.created_at,
        ))
    return out


@router.get(
    "/{user_id}/{name}",
    response_model=UserIngredientRead,
)
def get_user_ingredient(
    user_id: int,
    name:    str,
    session: Session = Depends(get_session),
):
    im = session.exec(
        select(IngredientMaster).where(IngredientMaster.name == name)
    ).first()
    if not im:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    ui = session.get(UserIngredient, (user_id, im.id))
    if not ui:
        raise HTTPException(status_code=404, detail="User ingredient not found")

    return UserIngredientRead(
        user_id    = ui.user_id,
        name       = name,
        quantity   = ui.quantity,
        created_at = ui.created_at,
    )


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
    im = session.exec(
        select(IngredientMaster).where(IngredientMaster.name == name)
    ).first()
    if not im:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    ui = session.get(UserIngredient, (user_id, im.id))
    if not ui:
        raise HTTPException(status_code=404, detail="User ingredient not found")

    ui.quantity = data.quantity
    session.add(ui); session.commit(); session.refresh(ui)

    return UserIngredientRead(
        user_id    = ui.user_id,
        name       = name,
        quantity   = ui.quantity,
        created_at = ui.created_at,
    )


@router.delete(
    "/{user_id}/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_ingredient(
    user_id: int,
    name:    str,
    session: Session = Depends(get_session),
):
    im = session.exec(
        select(IngredientMaster).where(IngredientMaster.name == name)
    ).first()
    if not im:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    ui = session.get(UserIngredient, (user_id, im.id))
    if not ui:
        raise HTTPException(status_code=404, detail="User ingredient not found")

    session.delete(ui)
    session.commit()
    return
