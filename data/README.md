# Data governance

`source_catalog.csv` is the auditable registry of candidate sources. Only entries marked `ready` are downloaded automatically, and only from allow-listed official domains.

Raw documents, extracted pages, chunks, and indexes are intentionally excluded from Git. Each downloaded file receives a SHA-256 checksum in `data/raw/download_report.json`.

A document with less than 50% extractable pages is excluded from the index until OCR is enabled. This prevents a scanned PDF cover or table of contents from masquerading as a complete legal source.

Before changing a source to `ready`, verify:

- the issuing authority and canonical URL;
- publication date and document version;
- whether the text is currently applicable or has amendments;
- access and reuse terms;
- that the document is not merely commentary about the law.

`evaluation_template.csv` is intentionally empty until questions and expected citations are reviewed against the official documents.
