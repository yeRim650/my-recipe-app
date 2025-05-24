# recipe_rag_pipeline.py
# -----------------------------------------------------------
# • RCP_PARTS_DTLS 원문 + 임베딩 저장
# • substring 재료 매칭
# • method·calories 필터 → qd.Filter/qd.FieldCondition 사용
# -----------------------------------------------------------
from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import os, logging, re, uuid, json, time, httpx, unicodedata
from typing import List, Optional
from urllib.parse import quote

from sentence_transformers import SentenceTransformer
from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy import update

from qdrant_client import QdrantClient, models as qd

# ───────── 설정 ───────────────────────────────────────────
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COL        = "recipes_bert_filtered"
API_KEY    = os.getenv("FOOD_SAFETY_API_KEY")
SERVICE_ID = os.getenv("FOOD_SAFETY_SERVICE_ID", "COOKRCP01")
BASE_URL   = "http://openapi.foodsafetykorea.go.kr/api"
DB_URL     = "sqlite:///example.db"
SEED_ING   = ["계란","두부","김치","우유","양파","대파","감자","당근","닭고기","돼지고기"]

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
log = logging.getLogger("pipeline")

# ───────── Qdrant 초기화 ──────────────────────────────────
qc = QdrantClient(url=QDRANT_URL)
if COL in [c.name for c in qc.get_collections().collections]:
    qc.delete_collection(collection_name=COL)

model = SentenceTransformer("all-MiniLM-L6-v2")
DIM = model.get_sentence_embedding_dimension()
qc.create_collection(
    collection_name=COL,
    vectors_config={"vector": qd.VectorParams(size=DIM, distance="Cosine")},
)
print(f"▶ Created collection '{COL}' (dim={DIM})")

# ───────── SQLModel 정의 ─────────────────────────────────
class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: Optional[str] = None
    method: Optional[str] = None       # RCP_WAY2
    parts_text: str                    # RCP_PARTS_DTLS 원문
    calories: Optional[int] = None
    embedding_id: Optional[str] = None
    recipe_hash: str

    def __repr__(self):
        return f"<Recipe {self.name!r}>"

engine = create_engine(DB_URL, echo=False)
SQLModel.metadata.create_all(engine)
with Session(engine) as db:
    db.exec(update(Recipe).values(embedding_id=None))
    db.commit()

def build_doc(r: Recipe) -> str:
    return f"{r.name} ({r.method or ''})\n재료: {r.parts_text}"

# ───────── 1) 레시피 수집 ─────────────────────────────────
def seed_core() -> None:
    if not API_KEY:
        raise RuntimeError("FOOD_SAFETY_API_KEY 필요")
    with Session(engine) as db:
        for ing in SEED_ING:
            url = f"{BASE_URL}/{API_KEY}/{SERVICE_ID}/json/1/100/RCP_PARTS_DTLS={quote(ing)}"
            rows = (
                httpx.get(url, timeout=10)
                .json()
                .get(SERVICE_ID, {})
                .get("row", [])
            )
            log.info("%s: %d건 수집", ing, len(rows))
            for it in rows:
                title = (it.get("RCP_NM") or "").strip()
                if not title:
                    continue
                # 중복 체크
                exists = db.exec(
                    select(Recipe).where(Recipe.recipe_hash == title)
                ).first()
                if exists:
                    continue

                db.add(Recipe(
                    name        = title,
                    category    = it.get("RCP_PAT2"),
                    method      = it.get("RCP_WAY2"),
                    parts_text  = unicodedata.normalize("NFKC", it.get("RCP_PARTS_DTLS","")).lower(),
                    calories    = int(float(it.get("INFO_ENG") or 0)),
                    recipe_hash = title,
                ))
            db.commit()

# ───────── 2) 임베딩 & 업서트 ─────────────────────────────
def embed(batch: int = 64) -> None:
    with Session(engine) as db:
        while True:
            recs = db.exec(
                select(Recipe).where(Recipe.embedding_id.is_(None)).limit(batch)
            ).all()
            if not recs:
                return

            docs = [build_doc(r) for r in recs]
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
                            "method":    r.method,
                            "calories":  r.calories,
                            "parts_text": r.parts_text,
                        },
                    )],
                )
                r.embedding_id = pid
            db.commit()
            log.info("업서트 %d건 완료", len(recs))
            time.sleep(0.05)

# ───────── 3) 추천 ───────────────────────────────────────
# 조리법 키워드 매핑
METHOD_MAP = {
    "볶음": "볶기", "볶아": "볶기", "볶": "볶기",
    "찌개": "끓이기", "국": "끓이기", "탕": "끓이기",
    "찜": "찌기", "구이": "굽기", "무침": "무침", "조림": "조림"
}

def parse_query(text: str):
    text_l = text.lower()

    # 1) 칼로리 패턴 (이상/이하)
    cal_m = re.search(r"(\d+)\s?k?cal", text_l)
    cal_cond: Optional[qd.FieldCondition] = None
    if cal_m:
        val = int(cal_m.group(1))
        # “이상” 아닌 경우 이하로 간주
        if re.search(r"이상|초과|over|more", text_l):
            cal_cond = qd.FieldCondition(
                key="calories",
                range=qd.Range(gte=val)
            )
        else:
            cal_cond = qd.FieldCondition(
                key="calories",
                range=qd.Range(lte=val)
            )

    # 2) 조리법 패턴
    meth_cond: Optional[qd.FieldCondition] = None
    for k, v in METHOD_MAP.items():
        if k in text_l:
            meth_cond = qd.FieldCondition(
                key="method",
                match=qd.MatchText(text=v)
            )
            break

    # 3) 벡터용 순수 질의
    # 제거할 패턴: 숫자 kcal 단위 + 조리법 키워드
    pattern = r"\d+\s?k?cal"
    pattern += "|" + "|".join(re.escape(k) for k in METHOD_MAP.keys())
    qtext = re.sub(pattern, "", text_l).strip()
    if not qtext:
        qtext = text_l

    # 4) Filter 객체 생성
    conds = []
    if cal_cond:
        conds.append(cal_cond)
    if meth_cond:
        conds.append(meth_cond)

    filt = qd.Filter(must=conds) if conds else None
    return filt, qtext

def substring_overlap(parts: str, fridge: List[str]) -> int:
    parts_l = parts.lower()
    return sum(1 for f in fridge if f.lower() in parts_l)

def recommend(user_text: str, fridge: List[str], k: int = 5) -> List[Recipe]:
    filt, qtext = parse_query(user_text)
    qv = model.encode([qtext], convert_to_list=True, normalize_embeddings=True)[0]

    resp = qc.query_points(
        collection_name=COL,
        query=qv,
        using="vector",
        query_filter=filt,
        limit=40,
        with_payload=True
    )
    hits = resp.points

    scored = []
    for h in hits:
        base = h.score
        # 재료 substring 가산
        bonus = 0.2 * substring_overlap(h.payload["parts_text"], fridge)
        # method 일치 소프트 가산
        if filt and any(isinstance(c, qd.FieldCondition) and c.key=="method"
                        and h.payload.get("method")==c.match.text
                        for c in filt.must):
            bonus += 0.3
        scored.append((base + bonus, h.payload["recipe_id"]))

    top_ids = [rid for _, rid in sorted(scored, reverse=True)[:k]]
    with Session(engine) as db:
        return db.exec(select(Recipe).where(Recipe.id.in_(top_ids))).all()

# ───────── main ─────────────────────────────────────────
if __name__ == "__main__":
    seed_core()   # 최초 1회: 수집
    embed()       # 최초 1회: 업서트

    results = recommend("100kcal 이상 국", ["감자"], k=3)
    print("◆ 추천 레시피:")
    for r in results:
        print(f"- {r.name} ({r.calories} kcal) — {r.parts_text[:60]}…")
