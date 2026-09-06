"""Conservative multilingual text normalization utilities."""

from __future__ import annotations

import re
import unicodedata


ARABIC_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670]")
ARABIC_CHARACTERS = re.compile(r"[\u0600-\u06FF]")
LATIN_CHARACTERS = re.compile(r"[A-Za-zÀ-ÿ]")
STOPWORDS = {
    "a", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle", "en",
    "est", "et", "il", "la", "le", "les", "ou", "par", "pour", "que", "quel", "quelle", "quels",
    "quelles", "qui", "sera", "sont", "sur", "un", "une",
    "ما", "من", "إلى", "الى", "على", "في", "عن", "هو", "هي", "هذا", "هذه", "و", "أو", "او",
}


def normalize_text(text: str) -> str:
    """Reduce extraction noise without rewriting legal terms."""
    text = unicodedata.normalize("NFKC", text)
    text = ARABIC_DIACRITICS.sub("", text)
    text = text.replace("ـ", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"\w+", normalize_text(text).lower(), flags=re.UNICODE)
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def detect_script(text: str) -> str:
    has_arabic = bool(ARABIC_CHARACTERS.search(text))
    has_latin = bool(LATIN_CHARACTERS.search(text))
    if has_arabic and has_latin:
        return "mixed"
    if has_arabic:
        return "arabic"
    if has_latin:
        return "latin"
    return "unknown"
