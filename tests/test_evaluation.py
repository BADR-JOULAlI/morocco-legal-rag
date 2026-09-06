from conftest import demo_chunks
from morocco_legal_rag.evaluation import (
    EvaluationQuestion,
    evaluate_retriever,
    ndcg_at_k,
    recall_at_k,
    reciprocal_rank,
)
from morocco_legal_rag.retrieval import HybridRetriever


def test_metrics() -> None:
    relevant = frozenset({"B"})
    assert recall_at_k(["A", "B"], relevant, 2) == 1.0
    assert reciprocal_rank(["A", "B"], relevant) == 0.5
    assert 0 < ndcg_at_k(["A", "B"], relevant, 2) < 1


def test_evaluate_retriever() -> None:
    retriever = HybridRetriever()
    retriever.fit(demo_chunks())
    questions = [
        EvaluationQuestion("q1", "délai traitement", frozenset({"A"})),
        EvaluationQuestion("q2", "demande écrite correction", frozenset({"B"})),
    ]
    metrics = evaluate_retriever(retriever, questions, k=2)
    assert metrics["recall_at_k"] == 1.0
    assert metrics["mrr"] == 1.0
