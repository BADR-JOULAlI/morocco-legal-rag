"""Extract and chunk downloaded PDFs while preserving catalog metadata."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pymupdf

from morocco_legal_rag.ingestion import extract_pdf, write_jsonl
from morocco_legal_rag.schemas import LegalChunk


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    catalog_path = project_root / "data" / "source_catalog.csv"
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    with catalog_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))

    all_chunks: list[LegalChunk] = []
    report: list[dict] = []
    enable_ocr = os.getenv("RAG_ENABLE_OCR", "false").lower() == "true"
    for row in rows:
        pdf_path = raw_dir / f"{row['source_id']}.pdf"
        if not pdf_path.exists():
            continue
        chunks, ocr_pages = extract_pdf(
            pdf_path,
            document_id=row["source_id"],
            title=row["title"],
            source_url=row["url"],
            publication_date=row["publication_date"],
            enable_ocr=enable_ocr,
        )
        with pymupdf.open(pdf_path) as document:
            page_count = document.page_count
        extraction_coverage = (page_count - len(ocr_pages)) / max(1, page_count)
        included = extraction_coverage >= 0.5
        if included:
            all_chunks.extend(chunks)
        report.append(
            {
                "source_id": row["source_id"],
                "file": str(pdf_path),
                "chunks": len(chunks),
                "page_count": page_count,
                "extraction_coverage": round(extraction_coverage, 4),
                "included_in_index": included,
                "pages_needing_ocr": ocr_pages,
            }
        )

    write_jsonl(all_chunks, processed_dir / "chunks.jsonl")
    (processed_dir / "ingestion_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"documents": len(report), "chunks": len(all_chunks)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
