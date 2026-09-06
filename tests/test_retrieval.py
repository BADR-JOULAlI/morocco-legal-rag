from conftest import demo_chunks
from morocco_legal_rag.retrieval import HybridRetriever


def test_hybrid_retrieval_finds_exact_legal_term() -> None:
    retriever = HybridRetriever()
    retriever.fit(demo_chunks())
    results = retriever.search("Quel est le délai de traitement ?", k=2)
    assert results[0].document_id == "A"
    assert results[0].lexical_rank == 1


def test_empty_index_returns_no_results() -> None:
    assert HybridRetriever().search("question") == []


def test_out_of_domain_question_abstains() -> None:
    retriever = HybridRetriever()
    retriever.fit(demo_chunks())
    assert retriever.search("Quelle météo demain à Casablanca ?") == []
