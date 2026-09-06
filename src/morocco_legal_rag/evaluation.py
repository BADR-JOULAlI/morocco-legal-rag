"""Deterministic retrieval metrics for reproducible RAG experiments."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .retrieval import HybridRetriever


@dataclass(frozen=True)
class EvaluationQuestion:
    question_id: str
    question: str
    relevant_source_ids: frozenset[str]
    language: str = "fr"


def recall_at_k(retrieved: list[str], relevant: frozenset[str], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(retrieved[:k]) & relevant) / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: frozenset[str]) -> float:
    for rank, source_id in enumerate(retrieved, start=1):
        if source_id in relevant:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[str], relevant: frozenset[str], k: int) -> float:
    gains = [1.0 if source_id in relevant else 0.0 for source_id in retrieved[:k]]
    dcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))
    ideal = [1.0] * min(len(relevant), k)
    idcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(ideal, start=1))
    return dcg / idcg if idcg else 0.0


def evaluate_retriever(
    retriever: HybridRetriever,
    questions: list[EvaluationQuestion],
    k: int = 5,
) -> dict[str, float]:
    if not questions:
        return {"recall_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0, "count": 0.0}
    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    ndcgs: list[float] = []
    for item in questions:
        results = retriever.search(item.question, k=k)
        retrieved = [result.document_id for result in results]
        recalls.append(recall_at_k(retrieved, item.relevant_source_ids, k))
        reciprocal_ranks.append(reciprocal_rank(retrieved, item.relevant_source_ids))
        ndcgs.append(ndcg_at_k(retrieved, item.relevant_source_ids, k))
    count = len(questions)
    return {
        "recall_at_k": sum(recalls) / count,
        "mrr": sum(reciprocal_ranks) / count,
        "ndcg_at_k": sum(ndcgs) / count,
        "count": float(count),
    }
