# app/ragu_embedding.py

import os
import re
import unicodedata
import logging
from typing import List, Optional

import torch
from transformers import AutoTokenizer, AutoModel
from qdrant_client import QdrantClient, models as qd
from sqlmodel import Session, select

from app.models import Recipe, Ingredient, IngredientMaster, RecipeEmbedding
from app.db import engine

logger = logging.getLogger("ragu_embedding")
logger.setLevel(logging.INFO)

# ─── HuggingFace KoSimCSE-BERT 모델 식별자 및 기기 설정
HF_MODEL_ID = "BM-K/KoSimCSE-bert"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 전역 변수에 None으로 초기화. 첫 호출 시에만 실제 로드하도록(=lazy loading)
_kosim_tokenizer: Optional[AutoTokenizer] = None
_kosim_model: Optional[AutoModel] = None


def load_kosimcse_model():
    """
    전역 변수(_kosim_tokenizer, _kosim_model)에 KoSimCSE-BERT를 로드하거나,
    이미 로드되어 있으면 그대로 반환합니다. (Lazy loading)
    """
    global _kosim_tokenizer, _kosim_model

    if _kosim_tokenizer is None or _kosim_model is None:
        logger.info(f"⏳ KoSimCSE-BERT 모델 로드 시도: {HF_MODEL_ID}")
        # 토크나이저 로드
        _kosim_tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_ID)
        # 모델 로드 (pooler_output을 사용하게 됨)
        _kosim_model = AutoModel.from_pretrained(HF_MODEL_ID)
        # GPU가 사용 가능하면 모델을 GPU로 옮김
        _kosim_model.to(DEVICE)
        # 평가 모드로 전환 (dropout 비활성화 등)
        _kosim_model.eval()
        logger.info(f"✅ KoSimCSE-BERT 모델 로드 완료: {HF_MODEL_ID}")

    return _kosim_tokenizer, _kosim_model


def get_qdrant_client() -> QdrantClient | None:
    """
    Qdrant에 연결을 시도합니다. 실패 시 None을 반환합니다.
    """
    try:
        qc = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        return qc
    except Exception as e:
        logger.warning(f"Qdrant 연결 실패: {e}")
        return None


def _normalize(text: str) -> str:
    """
    입력 텍스트를 NFKC 정규화한 뒤, 불필요한 공백을 하나로 줄이고 소문자로 변환합니다.
    """
    t = unicodedata.normalize("NFKC", text or "")
    return re.sub(r"\s+", " ", t).strip().lower()


def build_doc(r: Recipe, ing_names: List[str]) -> str:
    """
    레시피 객체와 재료 이름 목록을 받아 SBERT 임베딩용 태그 문서를 생성합니다.
    """
    tags = [
        f"[레시피명:{_normalize(r.name)}]",
        f"[조리법:{_normalize(r.method or '미정')}]",
        f"[요리종류:{_normalize(r.category or '미정')}]"
    ] + [f"[재료:{', '.join(ing_names)}]"]

    summary = f"{r.name}는 {r.category or '미정'}이며 {r.method or '미정'} 만드는 요리이다."
    return " ".join(tags) + " " + summary


def embed_and_upsert_single_recipe(recipe_id: int) -> None:
    """
    1) KoSimCSE-BERT 토크나이저/모델 로드 (lazy)
    2) DB에서 Recipe와 연관 재료 목록을 가져와 문서(build_doc) 생성
    3) KoSimCSE-BERT → pooler_output(MIND=768) 임베딩 벡터 생성
    4) Qdrant에 upsert, RecipeEmbedding 테이블에 저장
    """
    # 1) 모델과 토크나이저 로드
    tokenizer, model = load_kosimcse_model()

    # 2) DB에서 레시피와 재료 정보 조회
    with Session(engine) as db:
        r = db.get(Recipe, recipe_id)
        if not r:
            return

        rows = db.exec(
            select(Ingredient.recipe_id, IngredientMaster.name)
            .join(IngredientMaster, Ingredient.master_id == IngredientMaster.id)
            .where(Ingredient.recipe_id == recipe_id)
        ).all()
        ing_names = [iname for (_rid, iname) in rows]

        # 문서 생성
        doc = build_doc(r, ing_names)

        # 3) KoSimCSE-BERT 토크나이즈 및 임베딩
        encoded = tokenizer(
            [doc],               # 배치 크기 1
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        # 입력 텐서를 DEVICE로 옮기기
        encoded = {k: v.to(DEVICE) for k, v in encoded.items()}

        with torch.no_grad():
            outputs = model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
                # KoSimCSE-BERT는 token_type_ids 없이 동작
            )
            # SimCSE 방식: pooler_output을 임베딩으로 사용
            emb_tensor = outputs.pooler_output  # shape = (1, hidden_size)

        # CPU로 옮겨서 리스트로 변환
        emb = emb_tensor.cpu().numpy()[0].tolist()  # (1, 768) → (768,) 리스트

        # 4) Qdrant에 업서트
        qc = get_qdrant_client()
        if qc:
            try:
                point = qd.PointStruct(
                    id=recipe_id,
                    vector={"vector": emb},
                    payload={
                        "recipe_id": r.id,
                        "name":      r.name,
                        "category":  r.category,
                        "method":    r.method,
                    },
                )
                qc.upsert(collection_name="recipes_bert_vector", points=[point])
            except Exception as e:
                logger.error(f"Qdrant 업서트 오류 (recipe_id={recipe_id}): {e}")
        else:
            logger.warning(f"Qdrant 연결 불가, 업서트 건너뜀 (recipe_id={recipe_id})")

        # 5) RecipeEmbedding 테이블에 저장 (기존 엔트리가 있으면 덮어쓰기)
        from sqlalchemy.exc import IntegrityError

        rec_emb = RecipeEmbedding(recipe_id=recipe_id, embedding=emb)
        db.add(rec_emb)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.exec(
                select(RecipeEmbedding).where(RecipeEmbedding.recipe_id == recipe_id)
            ).first()
            if existing:
                existing.embedding = emb
                db.add(existing)
                db.commit()


if __name__ == "__main__":
    """
    1) 이 파일을 스크립트로 직접 실행하면, 아직 임베딩되지 않은 레시피 전체를 처리하는
       embed_new_recipes() 함수를 호출합니다.
    """
    from app.recipe_rag_pipeline import embed_new_recipes
    embed_new_recipes()
