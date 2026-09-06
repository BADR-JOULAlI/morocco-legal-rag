"""Application service joining retrieval, generation, and citations."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .generation import (
    ExtractiveGenerator,
    Generator,
    OpenAICompatibleGenerator,
    citations_from_contexts,
)
from .retrieval import HybridRetriever, SentenceTransformerEncoder
from .schemas import AskResponse, LegalChunk


class LegalRAGService:
    def __init__(self, retriever: HybridRetriever, generator: Generator) -> None:
        self.retriever = retriever
        self.generator = generator

    def ask(self, question: str, language: str = "fr", top_k: int = 5) -> AskResponse:
        contexts = self.retriever.search(question, k=top_k)
        answerable = bool(contexts and any(item.score > 0 for item in contexts))
        if not answerable:
            contexts = []
        answer = self.generator.generate(question, contexts, language)
        return AskResponse(
            answer=answer,
            citations=citations_from_contexts(contexts),
            answerable=answerable,
            language=language,
        )


def load_chunks(path: Path) -> list[LegalChunk]:
    if not path.exists():
        return []
    return [LegalChunk.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line]


def build_service(chunks_path: Path | None = None) -> LegalRAGService:
    encoder_name = os.getenv("RAG_ENCODER", "hashing").lower()
    encoder = SentenceTransformerEncoder() if encoder_name == "multilingual-e5" else None
    retriever = HybridRetriever(encoder=encoder)
    chunks = load_chunks(chunks_path) if chunks_path else []
    retriever.fit(chunks)
    endpoint = os.getenv("RAG_LLM_ENDPOINT", "").strip()
    model = os.getenv("RAG_LLM_MODEL", "").strip()
    generator: Generator
    if endpoint and model:
        generator = OpenAICompatibleGenerator(
            endpoint=endpoint,
            model=model,
            api_key=os.getenv("RAG_LLM_API_KEY", ""),
        )
    else:
        generator = ExtractiveGenerator()
    return LegalRAGService(retriever, generator)
