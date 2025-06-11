# recipe_rag_pipeline.py
from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import os, uuid, time, logging, re, unicodedata
from typing import List, Dict

from sentence_transformers import SentenceTransformer
from sqlmodel import SQLModel, Session, select, create_engine
from qdrant_client import QdrantClient, models as qd
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func


# ───────── 기본 설정 ──────────────────────────────────────
DB_URL      = os.getenv("DATABASE_URL", "sqlite:///example.db")
QDRANT_URL  = os.getenv("QDRANT_URL",  "http://localhost:6201")
COL         = "recipes_bert_vector"

MODEL_NAME  = "BM-K/KoSimCSE-bert"
BATCH_SIZE  = 64

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
log = logging.getLogger("engine")

# ───────── DB 모델 ────────────────────────────────────────
from app.models import (
    Recipe, Ingredient, IngredientMaster,
    RecipeEmbedding, UserIngredient, IngredientRecipeMapping
)

engine = create_engine(DB_URL, echo=False)

# ───────── Qdrant & SBERT ─────────────────────────────────
qc    = QdrantClient(QDRANT_URL)
model = SentenceTransformer(MODEL_NAME)
DIM   = model.get_sentence_embedding_dimension()

def reset_qdrant():
    """콜렉션을 새로 시작하고 싶을 때만 호출하세요."""
    if COL in [c.name for c in qc.get_collections().collections]:
        qc.delete_collection(collection_name=COL)
    qc.create_collection(
        collection_name=COL,
        vectors_config={"vector": qd.VectorParams(size=DIM, distance="Cosine")}
    )
    log.info("Qdrant 컬렉션 초기화 완료")

# ───────── build_doc: 태그 기반 문서 ──────────────────────
def _norm(txt: str) -> str:
    txt = unicodedata.normalize("NFKC", txt or "")
    return re.sub(r"\s+", " ", txt).strip().lower()

def build_doc(r: Recipe, ing_names: List[str]) -> str:
    tags = [
        f"[레시피명:{_norm(r.name)}]",
        f"[조리법:{_norm(r.method or '미정')}]",
        f"[요리종류:{_norm(r.category or '미정')}]"
    ] + [f"[재료:{r.description}]"]

    summary = f"{r.name}는 {r.category or '미정'}이며 {r.method or '미정'} 만드는 요리이다."
    return " ".join(tags) + " " + summary

# ───────── 1) 신규 레시피 임베딩 & 업서트 ────────────────
def embed_new_recipes(batch: int = BATCH_SIZE):
    with Session(engine) as db:
        subq = select(RecipeEmbedding.recipe_id)  # 이미 임베딩된 레시피 id

        while True:
            recs: List[Recipe] = db.exec(
                select(Recipe)
                .where(~Recipe.id.in_(subq))
                .limit(batch)
            ).all()
            if not recs:
                break

            rid_list = [r.id for r in recs]

            # 재료 이름 매핑
            ing_map: Dict[int, List[str]] = {}
            rows = db.exec(
                select(Ingredient.recipe_id, IngredientMaster.name)
                .join(IngredientMaster, Ingredient.master_id == IngredientMaster.id)
                .where(Ingredient.recipe_id.in_(rid_list))
            ).all()

            for rid, iname in rows:
                ing_map.setdefault(rid, []).append(iname)

            # 임베딩
            docs = [build_doc(r, ing_map.get(r.id, [])) for r in recs]
            vecs = model.encode(docs, convert_to_list=True, normalize_embeddings=True)

            for r, v in zip(recs, vecs):
                pid = str(uuid.uuid4())
                qc.upsert(
                    collection_name=COL,
                    points=[qd.PointStruct(
                        id=pid,
                        vector={"vector": v},
                        payload={
                            "recipe_id": r.id,
                            "name":      r.name,
                            "category":  r.category,
                            "method":    r.method
                        }
                    )]
                )
                db.add(RecipeEmbedding(recipe_id=r.id, embedding=v.tolist()))

            try:
                db.commit()
            except IntegrityError:
                db.rollback()

            log.info("업서트 %d건 완료", len(recs))
            time.sleep(0.05)

# ───────── 2) 사용자 맞춤 추천 ────────────────────────────
def recommend_for_user(user_id: int, query: str, top_k: int = 10, boost: float = 0.2):
    # 1) 사용자 냉장고 재료 ID 조회
    with Session(engine) as db:
        fridge_ids: list[int] = db.exec(
            select(IngredientMaster.id)
            .join(UserIngredient, IngredientMaster.id == UserIngredient.ingredient_id)
            .where(UserIngredient.user_id == user_id)
        ).all()

    # 2) 벡터 검색
    qv = model.encode([query], normalize_embeddings=True)[0]
    resp = qc.query_points(COL, query=qv, using="vector", limit=40, with_payload=True)

    # 3) 검색된 레시피 ID 리스트
    resp_rids = [p.payload["recipe_id"] for p in resp.points]

    # 4) IngredientRecipeMapping 으로 overlap 카운트 조회
    with Session(engine) as db:
        rows: list[tuple[int,int]] = db.exec(
            select(
                IngredientRecipeMapping.recipe_id,
                func.count(IngredientRecipeMapping.ingredient_id)
            )
            .where(
                IngredientRecipeMapping.recipe_id.in_(resp_rids),
                IngredientRecipeMapping.ingredient_id.in_(fridge_ids)
            )
            .group_by(IngredientRecipeMapping.recipe_id)
        ).all()

    # recipe_id → 겹친 재료 수 매핑
    overlap_count = {rid: cnt for rid, cnt in rows}

    # 5) score 계산
    scored: list[tuple[float,int]] = []
    for p in resp.points:
        rid = p.payload["recipe_id"]
        overlap = overlap_count.get(rid, 0)
        score = p.score + boost * overlap
        scored.append((score, rid))

    # 6) 내림차순 정렬 & top_k 고유 추출
    unique_rids: list[int] = []
    seen = set()
    for score, rid in sorted(scored, key=lambda x: x[0], reverse=True):
        if rid not in seen:
            seen.add(rid)
            unique_rids.append(rid)
        if len(unique_rids) >= top_k:
            break

    # 7) DB에서 레시피 일괄 조회
    with Session(engine) as db:
        recipes = db.exec(
            select(Recipe).where(Recipe.id.in_(unique_rids))
        ).all()

    # 8) 원래 order 대로 재정렬
    recipe_map = {r.id: r for r in recipes}
    ordered_recipes = [recipe_map[rid] for rid in unique_rids if rid in recipe_map]

    return ordered_recipes
# ───────── main ─────────────────────────────────────────
if __name__ == "__main__":
    # reset_qdrant()
    embed_new_recipes()

    for r in recommend_for_user(1, "파스타", 20):
        print(f"- {r.id} | {r.name} | {r.method} | {r.category}")
