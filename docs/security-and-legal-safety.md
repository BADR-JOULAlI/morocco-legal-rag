# Security and legal-safety boundaries

This repository is a research and portfolio project, not a legal-advice service.

## Required controls

- Answer only from retrieved and displayed evidence.
- Attach document ID and page number to every material claim.
- Abstain when no relevant passage is retrieved.
- Preserve publication date, source URL, authority, and SHA-256 checksum.
- Never silently merge historical and current versions of a text.
- Treat downloaded documents as untrusted input.
- Reject sources outside the explicit official-domain allow-list.
- Keep credentials out of notebooks, logs, and Git history.
- Require human review before using an evaluation question as ground truth.

## Known limitations

- A high retrieval score does not prove that a rule is currently applicable.
- OCR can alter numbers, article references, names, and punctuation.
- Translation into Darija may simplify or distort a legal concept.
- A citation can be syntactically valid while failing to support the claim.
- The extractive fallback improves traceability but is not a substitute for legal interpretation.
