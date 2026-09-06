"""Page-aware chunking that preserves source provenance."""

from __future__ import annotations

import hashlib

from .schemas import LegalChunk
from .text import normalize_text


def make_chunk_id(document_id: str, page: int, index: int, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{document_id}:p{page}:c{index}:{digest}"


def chunk_page(
    *,
    document_id: str,
    title: str,
    page: int,
    text: str,
    source_url: str = "",
    language: str = "unknown",
    publication_date: str = "",
    sha256: str = "",
    size: int = 260,
    overlap: int = 50,
) -> list[LegalChunk]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Expected size > 0 and 0 <= overlap < size")
    words = normalize_text(text).split()
    if not words:
        return []
    chunks: list[LegalChunk] = []
    step = size - overlap
    for index, start in enumerate(range(0, len(words), step)):
        chunk_text = " ".join(words[start : start + size])
        chunks.append(
            LegalChunk(
                id=make_chunk_id(document_id, page, index, chunk_text),
                document_id=document_id,
                title=title,
                page=page,
                text=chunk_text,
                source_url=source_url,
                language=language,
                publication_date=publication_date,
                sha256=sha256,
            )
        )
    return chunks
