"""
seed_recipes.py
──────────────────────────────────────────────────
· 배포(또는 로컬 초기화) 시 코어 레시피 - 약 1,000건 - 을
  Postgres + SQLModel 테이블에 선삽입(seeding)합니다.
· FastAPI 프로젝트 루트에서:
      $ python seed_recipes.py
──────────────────────────────────────────────────
"""
from __future__ import annotations

import logging
import os
import sys
import time
from typing import Dict, List
from urllib.parse import quote

import httpx
from sqlmodel import Session, select

# ────────────────────────────────────────────────
# 내부 모듈 import
from app.db import engine
from app.models import (
    IngredientMaster,
    Recipe,
    IngredientRecipeMapping,
    Instruction,
)
from app.routers.user_ingredients import parse_parts_dtls  # 기존 util 재사용

# ────────────────────────────────────────────────
# 환경 변수
API_KEY: str | None = os.getenv("FOOD_SAFETY_API_KEY")
SERVICE_ID: str = os.getenv("FOOD_SAFETY_SERVICE_ID", "COOKRCP01")

# 시드용 검색 키워드(10개 × 100건 ≒ 1 000 레시피)
SEED_INGREDIENTS: List[str] = [
    "계란", "두부", "김치", "우유", "양파",
    "대파", "감자", "당근", "닭고기", "돼지고기",
]

BASE_URL = "http://openapi.foodsafetykorea.go.kr/api"
PAGE_SIZE = 100                       # 1 ~ 100 row
REQUEST_TIMEOUT = 10                  # 초

log = logging.getLogger("seed_recipes")
logging.basicConfig(level=logging.INFO, format="%(levelname)s › %(message)s")


# ────────────────────────────────────────────────
# 헬퍼
def fetch_json(url: str) -> Dict:
    """단순 GET → JSON(dict), 오류 시 {} 반환."""
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            r = client.get(url)
        if r.status_code != 200:
            log.error("HTTP %s - %s", r.status_code, url)
            return {}
        return r.json()
    except (httpx.HTTPError, ValueError) as e:
        log.error("요청/파싱 오류: %s – %s", e, url)
        return {}


def ensure_ingredient_master(db: Session, name: str) -> IngredientMaster:
    """중복 확인 후 IngredientMaster 행을 확보·반환."""
    im = db.exec(select(IngredientMaster).where(IngredientMaster.name == name)).first()
    if not im:
        im = IngredientMaster(name=name)
        db.add(im)
        db.commit()
        db.refresh(im)
    return im


def ingest_one_item(db: Session, item: Dict) -> None:
    """
    단일 레시피(JSON row) ↦ Recipe / IngredientRecipeMapping / Instruction 삽입.
    기존에 동일한 recipe_hash(여기선 제목) 가 있으면 skip.
    """
    title: str | None = item.get("RCP_NM")
    if not title:
        return

    recipe_hash = title  # 👉 ‘제목’만으로 단순 중복 방지

    recipe: Recipe | None = db.exec(
        select(Recipe).where(Recipe.recipe_hash == recipe_hash)
    ).first()

    is_new = recipe is None
    if is_new:
        recipe = Recipe(
            name=title,
            category=item.get("RCP_PAT2"),        # e.g. 밥/죽/떡
            method=item.get("RCP_WAY2"),          # e.g. 끓이기 / 볶기
            description=item.get("RCP_PARTS_DTLS"),
            calories=_int(item.get("INFO_ENG")),
            protein=_int(item.get("INFO_PRO")),
            carbs=_int(item.get("INFO_CAR")),
            fat=_int(item.get("INFO_FAT")),
            sodium=_int(item.get("INFO_NA")),
            recipe_hash=recipe_hash,
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)

    # ── (1) 재료 매핑 ───────────────────────────
    # 새 레시피인 경우에만 parse 후 IngredientRecipeMapping 삽입
    if is_new:
        for ing_name, _, _ in parse_parts_dtls(item.get("RCP_PARTS_DTLS", "")):
            im = ensure_ingredient_master(db, ing_name)
            exists = db.exec(
                select(IngredientRecipeMapping)
                .where(
                    IngredientRecipeMapping.recipe_id == recipe.id,
                    IngredientRecipeMapping.ingredient_id == im.id,
                )
            ).first()
            if not exists:
                db.add(
                    IngredientRecipeMapping(
                        recipe_id=recipe.id,
                        ingredient_id=im.id,
                    )
                )

    # ── (2) 조리 순서(Instructions) ───────────────
    # MANUAL01 ··· MANUAL20 → step 1 ~ 20
    if is_new:
        blank = 0
        for i in range(1, 21):
            txt = (item.get(f"MANUAL{i:02d}") or "").strip()
            if not txt:
                blank += 1
                if blank >= 2:
                    break
                continue
            blank = 0
            already = db.exec(
                select(Instruction).where(
                    Instruction.recipe_id == recipe.id,
                    Instruction.step == i,
                )
            ).first()
            if not already:
                db.add(
                    Instruction(
                        recipe_id=recipe.id,
                        step=i,
                        instruction=txt,
                    )
                )

    db.commit()  # flush + commit 한 번에


def _int(text: str | None) -> int | None:
    """빈 문자열 → None, 그 외 int 변환."""
    try:
        return int(float(text)) if text and text.strip() else None
    except ValueError:
        return None


# ────────────────────────────────────────────────
# 메인 루프
def seed() -> None:
    if not API_KEY:
        sys.exit("❌  환경변수 FOOD_SAFETY_API_KEY 가 필요합니다.")

    with Session(engine) as db:
        for kwd in SEED_INGREDIENTS:
            log.info("▶  %s (max %d rows)", kwd, PAGE_SIZE)
            url = (
                f"{BASE_URL}/{API_KEY}/{SERVICE_ID}/json/1/{PAGE_SIZE}"
                f"/RCP_PARTS_DTLS={quote(kwd)}"
            )
            rows: List[dict] = (
                fetch_json(url).get(SERVICE_ID, {}).get("row", []) or []
            )
            log.info("   ↳  가져온 레시피 %d건", len(rows))
            for item in rows:
                try:
                    ingest_one_item(db, item)
                except Exception as e:  # 개별 레시피 오류는 계속 진행
                    log.warning("   ⚠︎  %s", e)
            # 분할 커밋은 ingest_one_item 내부에서 이루어짐
            time.sleep(0.25)  # API 부하 완화

    log.info("✔  시드 완료 – 스크립트 종료")


# ────────────────────────────────────────────────
if __name__ == "__main__":
    seed()
