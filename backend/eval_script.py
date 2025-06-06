#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
eval_script.py (RAG recommend_for_user 버전, query_text / gt_ids NaN 방지 포함)

사용 예시:
    python eval_script.py \
        --queries_csv evaluation_queries.csv \
        --k 5 \
        --user_id 1 \
        --output_results_csv eval_results.csv

이 스크립트는:
  1) `recipe_rag_pipeline.py` 에 정의된 recommend_for_user(user_id, query, top_k)을 호출하여
     실제 Qdrant+SBERT 기반으로 상위 K개 레시피를 가져오고,
  2) evaluation_queries.csv (query_id, query_text, gt_ids[, category]) 를 읽은 뒤,
  3) Precision@K, Recall@K, MAP@K 계산
  4) 결과를 콘솔에 출력하고, 원하면 CSV로 저장
"""

import argparse
import pandas as pd
from typing import List, Dict, Tuple

# ────── 추천 파이프라인에서 직접 가져오기 ─────────────────
# 같은 디렉토리에 recipe_rag_pipeline.py가 있다고 가정합니다.
# (만약 다른 경로에 있다면, PYTHONPATH를 설정하거나 import 경로를 수정하세요.)
from recipe_rag_pipeline import recommend_for_user


def load_queries(queries_csv_path: str) -> pd.DataFrame:
    """
    evaluation_queries.csv 파일을 읽어서 DataFrame으로 반환합니다.
    필수 컬럼:
      - query_id    (string)
      - query_text  (string)
      - gt_ids      (","로 구분된 string)
      - category    (string, 선택)
    반환된 DataFrame에 'gt_list'라는 컬럼이 추가되어,
    gt_ids 문자열을 파싱한 list[str]가 담겨 있습니다.
    """
    # CSV 헤더나 값에 앞뒤 공백이 있을 수 있으므로 `skipinitialspace=True`를 추가
    queries = pd.read_csv(
        queries_csv_path,
        dtype={"query_id": str, "gt_ids": str},
        skipinitialspace=True
    )
    # 컬럼명에 공백이 있다면 strip
    queries.columns = queries.columns.str.strip()

    # query_id: 문자열 형태로 통일
    queries["query_id"] = queries["query_id"].astype(str)

    # query_text 컬럼이 없으면 빈 문자열 컬럼을 만들고, 있으면 NaN을 빈 문자열로 대체
    if "query_text" not in queries.columns:
        queries["query_text"] = ""
    else:
        queries["query_text"] = queries["query_text"].fillna("").astype(str)

    # gt_ids 컬럼이 없으면 빈 문자열 컬럼을 만들고, 있으면 NaN을 빈 문자열로 대체
    if "gt_ids" not in queries.columns:
        queries["gt_ids"] = ""
    else:
        queries["gt_ids"] = queries["gt_ids"].fillna("")

    def parse_gt_ids(gt_str: str) -> List[str]:
        return [x.strip() for x in gt_str.split(",") if x.strip()]

    queries["gt_list"] = queries["gt_ids"].apply(parse_gt_ids)
    return queries


def average_precision_at_k(
    retrieved: List[str], ground_truth: List[str], k: int
) -> float:
    """
    한 쿼리에 대한 AP@K 계산:
      - ground_truth가 비어 있으면 0.0 반환
      - AP = (1 / |GT|) * sum_{i=1..k} [P(i) * rel(i)]
      - rel(i) = 1 if retrieved[i-1] ∈ ground_truth else 0
      - P(i) = (# relevant in top i) / i
    """
    if not ground_truth:
        return 0.0
    hits = 0
    score_sum = 0.0
    for i, rid in enumerate(retrieved[:k], start=1):
        if rid in ground_truth:
            hits += 1
            score_sum += hits / i
    return score_sum / len(ground_truth)


def precision_at_k(retrieved: List[str], ground_truth: List[str], k: int) -> float:
    """
    Precision@K = (# relevant in top K) / K
    """
    if k == 0:
        return 0.0
    rel_count = sum(1 for rid in retrieved[:k] if rid in ground_truth)
    return rel_count / k


def recall_at_k(retrieved: List[str], ground_truth: List[str], k: int) -> float:
    """
    Recall@K = (# relevant in top K) / |ground_truth|
    ground_truth이 비어 있으면 0.0 반환
    """
    if not ground_truth:
        return 0.0
    rel_count = sum(1 for rid in retrieved[:k] if rid in ground_truth)
    return rel_count / len(ground_truth)


def evaluate(
    queries_df: pd.DataFrame, user_id: int, k: int
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    모든 쿼리에 대해 recommend_for_user(user_id, query_text, k)을 호출하여
    상위 K개 레시피를 얻은 뒤 Precision@K, Recall@K, AP@K을 계산합니다.

    반환:
      1) results_df: per-query 결과 DataFrame 
         (각 행: query_id, query_text, gt_ids, retrieved_ids, precision_at_k, recall_at_k, avg_precision_at_k)
      2) metrics: 전체 메트릭 딕셔너리
         - mean_precision_at_K
         - mean_recall_at_K
         - MAP@K
    """
    rows = []
    precisions = []
    recalls = []
    average_precisions = []

    for _, qrow in queries_df.iterrows():
        qid = qrow["query_id"]
        qtext = qrow["query_text"]  # 이미 빈 문자열로 채워져 있음
        gt_list = qrow["gt_list"]

        # ==================================================================
        # 여기가 핵심: recommend_for_user(user_id, qtext, top_k)를 실제 호출
        # (리턴되는 것은 sqlalchemy 모델 Recipe 객체 리스트라고 가정)
        # ==================================================================
        recipes = recommend_for_user(user_id=user_id, query=qtext, top_k=k)
        # Recipe 객체에서 .id 속성(또는 PK)을 꺼내서 리스트로 변환
        retrieved_ids = [str(r.id) for r in recipes]

        prec = precision_at_k(retrieved_ids, gt_list, k)
        rec = recall_at_k(retrieved_ids, gt_list, k)
        ap = average_precision_at_k(retrieved_ids, gt_list, k)

        precisions.append(prec)
        recalls.append(rec)
        average_precisions.append(ap)

        rows.append(
            {
                "query_id": qid,
                "query_text": qtext,
                "gt_ids": ",".join(gt_list),
                "retrieved_ids": ",".join(retrieved_ids),
                f"precision_at_{k}": prec,
                f"recall_at_{k}": rec,
                f"avg_precision_at_{k}": ap,
            }
        )

    results_df = pd.DataFrame(rows)
    metrics = {
        f"mean_precision_at_{k}": sum(precisions) / len(precisions) if precisions else 0.0,
        f"mean_recall_at_{k}": sum(recalls) / len(recalls) if recalls else 0.0,
        f"MAP@{k}": sum(average_precisions) / len(average_precisions) if average_precisions else 0.0,
    }
    return results_df, metrics


def main():
    parser = argparse.ArgumentParser(
        description="(RAG recommend) 평가 스크립트: Precision@K, Recall@K, MAP@K"
    )
    parser.add_argument(
        "--queries_csv",
        required=True,
        help="Path to evaluation_queries.csv (query_id, query_text, gt_ids[, category])"
    )
    parser.add_argument(
        "--k", type=int, default=5, help="Compute top-K metrics (default: 5)"
    )
    parser.add_argument(
        "--user_id", type=int, required=True,
        help="추천을 수행할 사용자의 ID (recommend_for_user의 첫 번째 인자)"
    )
    parser.add_argument(
        "--output_results_csv",
        default=None,
        help="(Optional) Path to write per-query results (CSV)"
    )
    args = parser.parse_args()

    # 1) evaluation_queries.csv 읽기
    print(f"Loading queries from '{args.queries_csv}' ...")
    queries_df = load_queries(args.queries_csv)
    print(f"  → Loaded {len(queries_df)} queries.")

    # 2) 평가 수행 (RAG recommend_for_user 호출)
    print(f"Running evaluation (user_id={args.user_id}, K={args.k}) ...")
    results_df, metrics = evaluate(queries_df, args.user_id, args.k)

    print("\n=== Per-query Results (첫 5개 행) ===")
    print(results_df.head().to_string(index=False))

    if args.output_results_csv:
        print(f"\nWriting per-query results to '{args.output_results_csv}' ...")
        results_df.to_csv(args.output_results_csv, index=False)

    print("\n=== Aggregate Metrics ===")
    for name, val in metrics.items():
        print(f"{name}: {val:.4f}")


if __name__ == "__main__":
    main()
