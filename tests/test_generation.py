from conftest import demo_chunks
from morocco_legal_rag.generation import ExtractiveGenerator, build_grounded_prompt
from morocco_legal_rag.retrieval import HybridRetriever


def test_answer_contains_verifiable_citation() -> None:
    retriever = HybridRetriever()
    retriever.fit(demo_chunks())
    contexts = retriever.search("délai", k=1)
    answer = ExtractiveGenerator().generate("délai", contexts, "fr")
    assert "[Source A, page 1]" in answer


def test_prompt_requires_abstention_and_citations() -> None:
    prompt = build_grounded_prompt("question", [], "fr")
    assert "Cite chaque affirmation" in prompt
    assert "preuve est absente" in prompt
