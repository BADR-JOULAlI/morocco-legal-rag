"""Grounded answer generation with mandatory source citations."""

from __future__ import annotations

import re
from typing import Protocol

import requests

from .schemas import Citation, RetrievedChunk


DISCLAIMER = "Information documentaire uniquement — ne constitue pas un avis juridique."


def build_grounded_prompt(question: str, contexts: list[RetrievedChunk], language: str) -> str:
    language_name = {"fr": "français", "ar": "arabe", "darija": "darija"}[language]
    evidence = "\n\n".join(
        f"[Source {item.document_id}, page {item.page}]\n{item.text}"
        for item in contexts
    )
    return "\n\n".join(
        [
            "Tu es un assistant de recherche documentaire en droit marocain.",
            f"Réponds en {language_name} uniquement avec les extraits fournis.",
            "Cite chaque affirmation importante sous la forme [Source ID, page N].",
            "Si la preuve est absente, insuffisante, ancienne ou contradictoire, dis-le clairement.",
            "Ne donne pas de conseil juridique personnalisé et ne complète pas avec ta mémoire.",
            f"QUESTION : {question}",
            f"EXTRAITS :\n{evidence}",
        ]
    )


def citations_from_contexts(contexts: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            source_id=item.document_id,
            title=item.title,
            page=item.page,
            url=item.source_url,
            excerpt=item.text[:500],
            score=item.score,
            dense_score=item.dense_score,
            lexical_score=item.lexical_score,
            lexical_coverage=item.lexical_coverage,
        )
        for item in contexts
    ]


class Generator(Protocol):
    name: str

    def generate(self, question: str, contexts: list[RetrievedChunk], language: str) -> str: ...


class ExtractiveGenerator:
    name = "extractive-safe-fallback"

    def generate(self, question: str, contexts: list[RetrievedChunk], language: str) -> str:
        del question, language
        if not contexts:
            return "Les documents indexés ne permettent pas de répondre à cette question."
        lines = [
            f"{item.text} [Source {item.document_id}, page {item.page}]"
            for item in contexts[:3]
        ]
        return "\n\n".join(lines)


class OpenAICompatibleGenerator:
    """Works with any OpenAI-compatible /v1/chat/completions endpoint."""

    name = "openai-compatible"

    def __init__(self, *, endpoint: str, model: str, api_key: str = "", timeout: int = 90) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def generate(self, question: str, contexts: list[RetrievedChunk], language: str) -> str:
        prompt = build_grounded_prompt(question, contexts, language)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.post(
            f"{self.endpoint}/v1/chat/completions",
            headers=headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
        if contexts and not re.search(r"\[Source .+?, page \d+\]", answer):
            raise ValueError("The generator returned an answer without a verifiable citation")
        return answer
