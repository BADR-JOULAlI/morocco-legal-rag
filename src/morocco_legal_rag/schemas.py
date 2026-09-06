"""Shared data contracts for ingestion, retrieval, generation, and the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LegalChunk(BaseModel):
    id: str
    document_id: str
    title: str
    page: int = Field(ge=1)
    text: str
    source_url: str = ""
    language: str = "unknown"
    publication_date: str = ""
    sha256: str = ""


class RetrievedChunk(LegalChunk):
    score: float = Field(ge=0.0)
    dense_score: float = Field(default=0.0, ge=0.0)
    lexical_score: float = Field(default=0.0, ge=0.0)
    lexical_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    dense_rank: int | None = None
    lexical_rank: int | None = None


class Citation(BaseModel):
    source_id: str
    title: str
    page: int
    url: str = ""
    excerpt: str
    score: float = 0.0
    dense_score: float = 0.0
    lexical_score: float = 0.0
    lexical_coverage: float = 0.0


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    language: str = Field(default="fr", pattern="^(fr|ar|darija)$")
    top_k: int = Field(default=5, ge=1, le=20)


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    answerable: bool
    language: str
    warning: str = "Information documentaire uniquement — ne constitue pas un avis juridique."


class HealthResponse(BaseModel):
    status: str
    indexed_chunks: int
    generator: str
