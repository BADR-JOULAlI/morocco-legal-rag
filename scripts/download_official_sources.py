"""Download only catalog entries marked ready and hosted on official allow-listed domains."""

from pathlib import Path

from morocco_legal_rag.sources import download_catalog


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    results = download_catalog(
        project_root / "data" / "source_catalog.csv",
        project_root / "data" / "raw",
    )
    for result in results:
        print(result)
