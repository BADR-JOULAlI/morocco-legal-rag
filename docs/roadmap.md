# Roadmap

## Implemented locally

- auditable source catalog and allow-listed downloader;
- PDF hashing, page extraction, OCR flagging, and chunking;
- dependency-free BM25 and dense hashing baseline;
- reciprocal-rank fusion;
- multilingual grounded prompt and safe extractive fallback;
- OpenAI-compatible model adapter;
- FastAPI endpoints and Gradio evidence rail;
- deterministic retrieval evaluation;
- tests, Docker, and GitHub Actions configuration.

## Next validation gates

1. Download the approved official sample and record the checksum.
2. Review the extracted pages and OCR warnings.
3. Build the first reviewed evaluation set.
4. Compare the hashing baseline with multilingual-e5.
5. Add a reranker only if the benchmark demonstrates an improvement.
6. Replace the in-memory index with Qdrant after metadata filters are specified.
7. Add Ragas-based generation evaluation after a model endpoint is selected.
