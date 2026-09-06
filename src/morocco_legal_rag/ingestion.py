"""Auditable PDF extraction and page-aware chunk creation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .chunking import chunk_page
from .schemas import LegalChunk
from .text import detect_script


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_pdf(
    path: Path,
    *,
    document_id: str,
    title: str,
    source_url: str,
    publication_date: str = "",
    enable_ocr: bool = False,
    ocr_languages: str = "fra+ara",
) -> tuple[list[LegalChunk], list[int]]:
    import pymupdf

    checksum = sha256_file(path)
    chunks: list[LegalChunk] = []
    pages_needing_ocr: list[int] = []
    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if len(text) < 80:
                if enable_ocr:
                    try:
                        import pytesseract
                        from PIL import Image
                    except ImportError as error:
                        raise RuntimeError(
                            "OCR requested but pytesseract/Pillow are not installed. "
                            "Install the ocr extra and the Tesseract binary."
                        ) from error
                    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                    text = pytesseract.image_to_string(image, lang=ocr_languages).strip()
                if len(text) < 80:
                    pages_needing_ocr.append(page_number)
            chunks.extend(
                chunk_page(
                    document_id=document_id,
                    title=title,
                    page=page_number,
                    text=text,
                    source_url=source_url,
                    language=detect_script(text),
                    publication_date=publication_date,
                    sha256=checksum,
                )
            )
    return chunks, pages_needing_ocr


def write_jsonl(chunks: list[LegalChunk], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(json.dumps(chunk.model_dump(), ensure_ascii=False) for chunk in chunks) + "\n",
        encoding="utf-8",
    )
