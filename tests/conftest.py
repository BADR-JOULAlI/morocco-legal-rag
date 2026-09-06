from morocco_legal_rag.retrieval import HybridRetriever
from morocco_legal_rag.schemas import LegalChunk
from morocco_legal_rag.service import LegalRAGService
from morocco_legal_rag.generation import ExtractiveGenerator


def demo_chunks() -> list[LegalChunk]:
    return [
        LegalChunk(
            id="A:p1:c0",
            document_id="A",
            title="Document pédagogique A",
            page=1,
            text="Le délai pédagogique de traitement est de dix jours ouvrables.",
            source_url="https://example.invalid/a",
            language="fr",
        ),
        LegalChunk(
            id="B:p2:c0",
            document_id="B",
            title="Document pédagogique B",
            page=2,
            text="Une correction nécessite une demande écrite et un justificatif rectifié.",
            source_url="https://example.invalid/b",
            language="fr",
        ),
        LegalChunk(
            id="C:p4:c0",
            document_id="C",
            title="Document pédagogique C",
            page=4,
            text="Le dépôt pédagogique est disponible au guichet de démonstration.",
            source_url="https://example.invalid/c",
            language="fr",
        ),
    ]


def demo_service() -> LegalRAGService:
    retriever = HybridRetriever()
    retriever.fit(demo_chunks())
    return LegalRAGService(retriever, ExtractiveGenerator())
