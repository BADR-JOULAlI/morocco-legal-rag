"""Controlled downloader for allow-listed official Moroccan sources."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

import requests


ALLOWED_HOSTS = {"adala.justice.gov.ma", "www.sgg.gov.ma", "sgg.gov.ma"}


def safe_filename(source_id: str, url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower() or ".html"
    return f"{source_id}{suffix}"


def download_catalog(catalog_path: Path, output_dir: Path, max_attempts: int = 3) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report: list[dict] = []
    with catalog_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        if row.get("status") != "ready":
            continue
        host = urlparse(row["url"]).hostname or ""
        if host not in ALLOWED_HOSTS:
            report.append({"source_id": row["source_id"], "status": "blocked-host", "host": host})
            continue
        destination = output_dir / safe_filename(row["source_id"], row["url"])
        if destination.exists() and destination.stat().st_size > 0:
            report.append(
                {
                    "source_id": row["source_id"],
                    "status": "already-present",
                    "path": str(destination),
                    "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                }
            )
            continue
        temporary = destination.with_suffix(destination.suffix + ".part")
        last_error = "unknown error"
        for attempt in range(1, max_attempts + 1):
            temporary.unlink(missing_ok=True)
            try:
                with requests.get(
                    row["url"], timeout=(20, 120), allow_redirects=True, stream=True
                ) as response:
                    response.raise_for_status()
                    digest = hashlib.sha256()
                    downloaded = 0
                    with temporary.open("wb") as output:
                        for block in response.iter_content(chunk_size=1024 * 1024):
                            if not block:
                                continue
                            output.write(block)
                            digest.update(block)
                            downloaded += len(block)
                    expected = int(response.headers.get("content-length", downloaded))
                    if expected and downloaded != expected:
                        raise IOError(f"incomplete download: expected {expected}, received {downloaded}")
                    temporary.replace(destination)
                    report.append(
                        {
                            "source_id": row["source_id"],
                            "status": "downloaded",
                            "path": str(destination),
                            "sha256": digest.hexdigest(),
                            "content_type": response.headers.get("content-type", ""),
                            "attempt": attempt,
                        }
                    )
                    break
            except (requests.RequestException, OSError) as error:
                last_error = str(error)
        else:
            temporary.unlink(missing_ok=True)
            report.append(
                {
                    "source_id": row["source_id"],
                    "status": "failed",
                    "attempts": max_attempts,
                    "error": last_error,
                }
            )
    (output_dir / "download_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report
