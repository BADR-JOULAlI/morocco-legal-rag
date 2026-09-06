"""FastAPI application for the legal RAG service."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .schemas import AskRequest, AskResponse, HealthResponse
from .service import LegalRAGService, build_service
from .web import INDEX_HTML


def create_app(service: LegalRAGService | None = None) -> FastAPI:
    chunks_path = Path(os.getenv("RAG_CHUNKS_PATH", "data/processed/chunks.jsonl"))
    rag = service or build_service(chunks_path)
    app = FastAPI(
        title="Morocco Legal RAG",
        version="0.2.0",
        description="Research assistant for public Moroccan legal documents.",
    )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def index() -> str:
        return INDEX_HTML

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            indexed_chunks=len(rag.retriever.chunks),
            generator=rag.generator.name,
        )

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        return rag.ask(request.question, request.language, request.top_k)

    return app


app = create_app()


def run() -> None:
    uvicorn.run("morocco_legal_rag.api:app", host="0.0.0.0", port=8000, reload=False)
