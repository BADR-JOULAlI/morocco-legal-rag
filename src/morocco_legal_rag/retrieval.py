"""Hybrid dense + lexical retrieval with reciprocal-rank fusion."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from collections.abc import Sequence
from typing import Protocol

from .schemas import LegalChunk, RetrievedChunk
from .text import tokenize


class Encoder(Protocol):
    name: str

    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashingEncoder:
    """Dependency-free baseline encoder for tests and offline demonstrations."""

    name = "hashing-baseline"
    uses_e5_prefixes = False
    is_semantic = False

    def __init__(self, dimensions: int = 2048) -> None:
        self.dimensions = dimensions

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in tokenize(text):
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                position = int.from_bytes(digest, "big") % self.dimensions
                vector[position] += 1.0
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


class SentenceTransformerEncoder:
    name = "intfloat/multilingual-e5-base"
    uses_e5_prefixes = True
    is_semantic = True

    def __init__(self, model_name: str = name) -> None:
        from sentence_transformers import SentenceTransformer

        self.name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        values = self.model.encode(list(texts), normalize_embeddings=True)
        return values.tolist()


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    return max(0.0, sum(a * b for a, b in zip(left, right)))


class BM25Index:
    def __init__(self, documents: Sequence[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.tokens = [tokenize(document) for document in documents]
        self.lengths = [len(tokens) for tokens in self.tokens]
        self.average_length = sum(self.lengths) / max(1, len(self.lengths))
        self.term_frequencies = [Counter(tokens) for tokens in self.tokens]
        self.document_frequency = Counter(
            term for tokens in self.tokens for term in set(tokens)
        )

    def scores(self, query: str) -> list[float]:
        query_terms = tokenize(query)
        document_count = len(self.tokens)
        scores: list[float] = []
        for frequencies, length in zip(self.term_frequencies, self.lengths):
            score = 0.0
            for term in query_terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                df = self.document_frequency[term]
                idf = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * length / max(1.0, self.average_length)
                )
                score += idf * frequency * (self.k1 + 1) / denominator
            scores.append(score)
        return scores


class HybridRetriever:
    def __init__(
        self,
        encoder: Encoder | None = None,
        rrf_k: int = 60,
        semantic_threshold: float = 0.35,
        lexical_coverage_threshold: float = 0.4,
    ) -> None:
        self.encoder = encoder or HashingEncoder()
        self.rrf_k = rrf_k
        self.semantic_threshold = semantic_threshold
        self.lexical_coverage_threshold = lexical_coverage_threshold
        self.chunks: list[LegalChunk] = []
        self.vectors: list[list[float]] = []
        self.bm25 = BM25Index([])

    def fit(self, chunks: Sequence[LegalChunk]) -> None:
        self.chunks = list(chunks)
        prefix = "passage: " if getattr(self.encoder, "uses_e5_prefixes", False) else ""
        passages = [f"{prefix}{chunk.text}" for chunk in self.chunks]
        self.vectors = self.encoder.encode(passages) if passages else []
        self.bm25 = BM25Index([chunk.text for chunk in self.chunks])

    def search(
        self,
        query: str,
        *,
        k: int = 5,
        language: str | None = None,
    ) -> list[RetrievedChunk]:
        if not self.chunks:
            return []
        candidate_indices = [
            index
            for index, chunk in enumerate(self.chunks)
            if language is None or chunk.language in {language, "unknown", "mixed"}
        ]
        prefix = "query: " if getattr(self.encoder, "uses_e5_prefixes", False) else ""
        query_vector = self.encoder.encode([f"{prefix}{query}"])[0]
        dense_scores = {index: cosine(query_vector, self.vectors[index]) for index in candidate_indices}
        lexical_values = self.bm25.scores(query)
        lexical_scores = {index: lexical_values[index] for index in candidate_indices}
        query_terms = set(tokenize(query))
        lexical_coverage = {
            index: len(query_terms & set(self.bm25.tokens[index])) / max(1, len(query_terms))
            for index in candidate_indices
        }
        minimum_overlap = 1 if len(query_terms) <= 2 else 2
        candidate_indices = [
            index
            for index in candidate_indices
            if (
                (
                    lexical_scores[index] > 0
                    and len(query_terms & set(self.bm25.tokens[index])) >= minimum_overlap
                    and lexical_coverage[index] >= self.lexical_coverage_threshold
                )
                or (
                    getattr(self.encoder, "is_semantic", False)
                    and dense_scores[index] >= self.semantic_threshold
                )
            )
        ]
        if not candidate_indices:
            return []
        lexical_order = sorted(candidate_indices, key=lexical_scores.get, reverse=True)
        lexical_rank = {index: rank for rank, index in enumerate(lexical_order, start=1)}
        if getattr(self.encoder, "is_semantic", False):
            dense_order = sorted(candidate_indices, key=dense_scores.get, reverse=True)
            dense_rank = {index: rank for rank, index in enumerate(dense_order, start=1)}
            fused = {
                index: 1 / (self.rrf_k + dense_rank[index])
                + 1 / (self.rrf_k + lexical_rank[index])
                for index in candidate_indices
            }
        else:
            dense_rank = {}
            fused = {
                index: 1 / (self.rrf_k + lexical_rank[index])
                for index in candidate_indices
            }
        best = sorted(candidate_indices, key=fused.get, reverse=True)[:k]
        return [
            RetrievedChunk(
                **self.chunks[index].model_dump(),
                score=fused[index],
                dense_score=dense_scores[index],
                lexical_score=lexical_scores[index],
                lexical_coverage=lexical_coverage[index],
                dense_rank=dense_rank.get(index),
                lexical_rank=lexical_rank[index],
            )
            for index in best
        ]
