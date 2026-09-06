"""Generate the portfolio notebooks without requiring nbformat."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(source).strip().splitlines(True)}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip().splitlines(True),
    }


def write_notebook(name: str, cells: list[dict]) -> None:
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = NOTEBOOKS / name
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


COMMON = '''
from pathlib import Path

PROJECT_ROOT = Path.cwd()
if PROJECT_ROOT.name == "notebooks":
    PROJECT_ROOT = PROJECT_ROOT.parent

DATA = PROJECT_ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
INDEX = DATA / "index"
for directory in (RAW, PROCESSED, INDEX):
    directory.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT
'''


def main() -> None:
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)

    write_notebook("00_project_overview.ipynb", [
        md('''
        # Morocco Legal RAG — vue d'ensemble

        Ce notebook présente le problème, les garde-fous et l'architecture du système.

        **But :** répondre en français, arabe ou darija à partir de textes juridiques marocains, avec une citation vérifiable pour chaque réponse.

        **Limite essentielle :** l'application est un outil de recherche documentaire et ne fournit pas d'avis juridique.
        '''),
        code(COMMON),
        md('''
        ## Pipeline

        `sources officielles → PDF/OCR → normalisation → chunks → embeddings + BM25 → reranking → réponse → citations → évaluation`

        Les métadonnées conservées incluent le titre, l'autorité émettrice, la date, la langue, l'URL, la page et le hash du fichier.
        '''),
        code('''
        stages = {
            "collecte": "documents publics et provenance",
            "extraction": "texte natif puis OCR si nécessaire",
            "retrieval": "recherche dense + lexicale",
            "generation": "réponse limitée au contexte",
            "evaluation": "recall@k, MRR, fidélité et citations",
        }
        stages
        '''),
    ])

    write_notebook("01_source_catalog.ipynb", [
        md('''
        # 01 — Catalogue des sources

        On constitue d'abord un catalogue auditable. Aucun téléchargement massif n'est effectué sans vérifier les conditions d'accès et la provenance.
        '''),
        code(COMMON),
        code('''
        import pandas as pd

        columns = [
            "source_id", "title", "authority", "document_type", "language",
            "publication_date", "url", "accessed_at", "license_or_terms", "status"
        ]
        catalog_path = DATA / "source_catalog.csv"
        if catalog_path.exists():
            catalog = pd.read_csv(catalog_path)
        else:
            catalog = pd.DataFrame(columns=columns)
            catalog.to_csv(catalog_path, index=False)
        catalog
        '''),
        md('''
        ## Contrôles avant ingestion

        - domaine et autorité clairement identifiés ;
        - texte en vigueur distingué des anciennes versions ;
        - date d'accès conservée ;
        - URL directe vers le document ;
        - aucune interprétation ajoutée aux données sources.
        '''),
    ])

    write_notebook("02_pdf_extraction_ocr.ipynb", [
        md('''
        # 02 — Extraction PDF et OCR

        Extraction page par page avec PyMuPDF. Les pages contenant très peu de texte sont signalées pour un éventuel OCR.
        '''),
        code(COMMON),
        code('''
        import hashlib
        import json
        import fitz

        def sha256_file(path: Path) -> str:
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            return digest.hexdigest()

        def extract_pdf(path: Path) -> list[dict]:
            pages = []
            with fitz.open(path) as document:
                for page_number, page in enumerate(document, start=1):
                    text = page.get_text("text").strip()
                    pages.append({
                        "file": path.name,
                        "page": page_number,
                        "text": text,
                        "needs_ocr": len(text) < 80,
                        "sha256": sha256_file(path),
                    })
            return pages

        pdf_files = sorted(RAW.glob("*.pdf"))
        extracted = [page for pdf in pdf_files for page in extract_pdf(pdf)]
        output = PROCESSED / "pages.jsonl"
        with output.open("w", encoding="utf-8") as stream:
            for row in extracted:
                stream.write(json.dumps(row, ensure_ascii=False) + "\\n")
        {"pdf_count": len(pdf_files), "page_count": len(extracted), "output": str(output)}
        '''),
        md('''
        Pour les documents scannés, installer l'option `ocr` et Tesseract avec les langues arabe et française. L'OCR doit rester traçable : on conserve toujours le numéro de page et le PDF original.
        '''),
    ])

    write_notebook("03_text_cleaning_chunking.ipynb", [
        md('''
        # 03 — Nettoyage multilingue et découpage

        Normalisation prudente : on réduit le bruit sans modifier la portée juridique du texte. Le texte original reste conservé à côté du texte normalisé.
        '''),
        code(COMMON),
        code('''
        import json
        import re
        import unicodedata

        ARABIC_DIACRITICS = re.compile(r"[\\u0617-\\u061A\\u064B-\\u0652]")

        def normalize_text(text: str) -> str:
            text = unicodedata.normalize("NFKC", text)
            text = ARABIC_DIACRITICS.sub("", text)
            text = re.sub(r"[ \\t]+", " ", text)
            text = re.sub(r"\\n{3,}", "\\n\\n", text)
            return text.strip()

        def chunk_words(text: str, size: int = 260, overlap: int = 50) -> list[str]:
            words = text.split()
            if not words:
                return []
            step = max(1, size - overlap)
            return [" ".join(words[start:start + size]) for start in range(0, len(words), step)]

        pages_path = PROCESSED / "pages.jsonl"
        pages = []
        if pages_path.exists():
            pages = [json.loads(line) for line in pages_path.read_text(encoding="utf-8").splitlines()]

        chunks = []
        for page in pages:
            normalized = normalize_text(page["text"])
            for chunk_id, chunk in enumerate(chunk_words(normalized)):
                chunks.append({**page, "chunk_id": chunk_id, "text_normalized": chunk})

        chunks_path = PROCESSED / "chunks.jsonl"
        with chunks_path.open("w", encoding="utf-8") as stream:
            for row in chunks:
                stream.write(json.dumps(row, ensure_ascii=False) + "\\n")
        {"pages": len(pages), "chunks": len(chunks), "output": str(chunks_path)}
        '''),
    ])

    write_notebook("04_hybrid_index.ipynb", [
        md('''
        # 04 — Index hybride multilingue

        On combine les embeddings multilingues, efficaces pour le sens, avec BM25, utile pour les numéros d'articles et les termes juridiques exacts.
        '''),
        code(COMMON),
        code('''
        import json
        import pickle
        import numpy as np
        from rank_bm25 import BM25Okapi
        from sentence_transformers import SentenceTransformer

        chunks_path = PROCESSED / "chunks.jsonl"
        chunks = []
        if chunks_path.exists():
            chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines()]

        texts = [row["text_normalized"] for row in chunks]
        model_name = "intfloat/multilingual-e5-base"
        model = SentenceTransformer(model_name)
        embeddings = model.encode(
            [f"passage: {text}" for text in texts],
            normalize_embeddings=True,
            show_progress_bar=True,
        ) if texts else np.empty((0, 768), dtype="float32")

        np.save(INDEX / "embeddings.npy", embeddings)
        (INDEX / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
        bm25 = BM25Okapi([text.lower().split() for text in texts]) if texts else None
        with (INDEX / "bm25.pkl").open("wb") as stream:
            pickle.dump(bm25, stream)
        {"model": model_name, "documents": len(texts), "shape": embeddings.shape}
        '''),
    ])

    write_notebook("05_multilingual_rag.ipynb", [
        md('''
        # 05 — RAG multilingue avec citations

        Le retrieval hybride fusionne similarité dense et score BM25. La réponse doit reconnaître explicitement lorsque les documents ne suffisent pas.
        '''),
        code(COMMON),
        code('''
        import json
        import pickle
        import numpy as np
        from sentence_transformers import SentenceTransformer

        chunks = json.loads((INDEX / "chunks.json").read_text(encoding="utf-8"))
        embeddings = np.load(INDEX / "embeddings.npy")
        with (INDEX / "bm25.pkl").open("rb") as stream:
            bm25 = pickle.load(stream)
        encoder = SentenceTransformer("intfloat/multilingual-e5-base")

        def minmax(values: np.ndarray) -> np.ndarray:
            if len(values) == 0 or float(values.max() - values.min()) == 0:
                return np.zeros_like(values, dtype=float)
            return (values - values.min()) / (values.max() - values.min())

        def retrieve(question: str, k: int = 5, alpha: float = 0.65) -> list[dict]:
            query_vector = encoder.encode([f"query: {question}"], normalize_embeddings=True)[0]
            dense = embeddings @ query_vector
            lexical = np.asarray(bm25.get_scores(question.lower().split()))
            scores = alpha * minmax(dense) + (1 - alpha) * minmax(lexical)
            best = np.argsort(scores)[::-1][:k]
            return [{**chunks[i], "score": float(scores[i])} for i in best]

        question = "Quels documents répondent à ma question juridique ?"
        contexts = retrieve(question) if chunks else []
        [(c["file"], c["page"], round(c["score"], 3)) for c in contexts]
        '''),
        code('''
        def build_grounded_prompt(question: str, contexts: list[dict], language: str = "français") -> str:
            evidence = "\\n\\n".join(
                f"[Source {i} — {c['file']}, page {c['page']}]\\n{c['text_normalized']}"
                for i, c in enumerate(contexts, start=1)
            )
            instructions = [
                "Tu es un assistant de recherche documentaire en droit marocain.",
                f"Réponds en {language}. Utilise uniquement les extraits fournis.",
                "Cite chaque affirmation sous la forme [Source N].",
                "Si les sources sont insuffisantes ou contradictoires, dis-le clairement.",
                "Ne présente jamais la réponse comme un avis juridique professionnel.",
                f"Question : {question}",
                f"Extraits :\\n{evidence}",
            ]
            return "\\n\\n".join(instructions)

        prompt = build_grounded_prompt(question, contexts)
        print(prompt[:3000])
        '''),
        md('''
        La cellule suivante du projet pourra brancher un LLM local ou une API. Le prompt, le retrieval et les citations restent indépendants du fournisseur afin de faciliter les comparaisons.
        '''),
    ])

    write_notebook("06_rag_evaluation.ipynb", [
        md('''
        # 06 — Évaluation

        Un RAG juridique doit être évalué séparément sur la récupération, la qualité des citations et la fidélité au contexte.
        '''),
        code(COMMON),
        code('''
        import pandas as pd

        evaluation_path = DATA / "evaluation_questions.csv"
        columns = [
            "question_id", "question", "language", "expected_source",
            "expected_page", "answerable", "notes"
        ]
        if evaluation_path.exists():
            evaluation = pd.read_csv(evaluation_path)
        else:
            evaluation = pd.DataFrame(columns=columns)
            evaluation.to_csv(evaluation_path, index=False)
        evaluation
        '''),
        code('''
        def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
            if not relevant:
                return 0.0
            return len(set(retrieved[:k]) & relevant) / len(relevant)

        def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
            for rank, item in enumerate(retrieved, start=1):
                if item in relevant:
                    return 1.0 / rank
            return 0.0

        assert recall_at_k(["A", "B"], {"B"}, 2) == 1.0
        assert reciprocal_rank(["A", "B"], {"B"}) == 0.5
        '''),
        md('''
        ## Grille qualitative

        - la réponse est-elle entièrement soutenue par les extraits ?
        - chaque affirmation importante possède-t-elle une citation correcte ?
        - le système refuse-t-il de répondre lorsque la preuve manque ?
        - la réponse conserve-t-elle le même sens en français, arabe et darija ?
        - les anciennes versions d'un texte sont-elles clairement signalées ?
        '''),
    ])

    write_notebook("07_gradio_demo.ipynb", [
        md('''
        # 07 — Démonstration interactive

        Interface minimale pour présenter le projet dans un portfolio. Elle montre les passages récupérés et leurs pages avant d'ajouter la génération finale.
        '''),
        code(COMMON),
        code('''
        import gradio as gr

        def answer(question: str, language: str):
            if not question.strip():
                return "Veuillez saisir une question.", ""
            contexts = retrieve(question, k=5)
            sources = "\\n\\n".join(
                f"### {item['file']} — page {item['page']} — score {item['score']:.3f}\\n{item['text_normalized'][:700]}"
                for item in contexts
            )
            response = (
                "Les passages pertinents sont affichés à droite. "
                "La génération finale sera activée après validation du corpus et du modèle."
            )
            return response, sources

        demo = gr.Interface(
            fn=answer,
            inputs=[gr.Textbox(label="Question"), gr.Dropdown(["français", "العربية", "الدارجة"], value="français")],
            outputs=[gr.Markdown(label="Réponse"), gr.Markdown(label="Sources")],
            title="Morocco Legal RAG",
            description="Assistant documentaire multilingue — les résultats ne constituent pas un avis juridique.",
        )
        demo.launch(share=False)
        '''),
    ])

    write_notebook("08_rag_beginner_course.ipynb", [
        md('''
        # Comprendre le RAG — cours pour débutant

        Bienvenue ! Ce cours part de zéro et construit progressivement un mini-système RAG.

        À la fin, tu sauras expliquer :

        - pourquoi un LLM seul ne suffit pas toujours ;
        - comment préparer et découper des documents ;
        - ce que sont les embeddings et la recherche sémantique ;
        - comment créer un prompt fondé sur des sources ;
        - comment évaluer un RAG et réduire les hallucinations.

        Le mini-corpus utilisé ici est **fictif et uniquement pédagogique**. Il ne contient aucun conseil juridique.
        '''),
        md('''
        ## 1. L'idée en une phrase

        **RAG** signifie **Retrieval-Augmented Generation**, ou « génération augmentée par la recherche ».

        Imagine un étudiant pendant un examen :

        - un **LLM seul** répond avec ce qu'il a mémorisé ;
        - un **RAG** commence par ouvrir les bons documents, puis répond en s'appuyant dessus.

        Le RAG n'entraîne pas nécessairement un nouveau modèle. Il fournit au modèle un contexte pertinent au moment de la question.
        '''),
        md('''
        ![Comparaison entre un LLM seul et un système RAG](assets/llm_vs_rag.png)
        '''),
        md('''
        ## 2. Le pipeline complet

        Un système RAG suit généralement cinq étapes :

        1. l'utilisateur pose une question ;
        2. le système cherche les passages les plus proches ;
        3. il sélectionne les documents pertinents ;
        4. il donne ces passages au LLM comme contexte ;
        5. le LLM produit une réponse accompagnée de sources.
        '''),
        md('''
        ![Les cinq étapes d'un pipeline RAG](assets/rag_pipeline.png)
        '''),
        md('''
        ## 3. Notre mini-corpus

        Pour comprendre le mécanisme, nous allons utiliser quatre petits documents inventés. Dans un vrai projet, ils seraient remplacés par des PDF officiels avec titre, date, URL et numéro de page.
        '''),
        code(COMMON),
        code('''
        documents = [
            {
                "id": "DOC-A",
                "title": "Guide pédagogique des demandes",
                "page": 1,
                "text": "Une demande fictive doit contenir un formulaire signé et une copie du justificatif pédagogique.",
            },
            {
                "id": "DOC-B",
                "title": "Délais de traitement — exemple",
                "page": 3,
                "text": "Dans cet exemple fictif, le délai indicatif de traitement est de dix jours ouvrables.",
            },
            {
                "id": "DOC-C",
                "title": "Procédure de correction — exemple",
                "page": 2,
                "text": "Une erreur dans le dossier pédagogique peut être corrigée avec une demande écrite et le document rectifié.",
            },
            {
                "id": "DOC-D",
                "title": "Canaux de dépôt — exemple",
                "page": 4,
                "text": "Le dépôt fictif peut être effectué au guichet pédagogique ou sur la plateforme de démonstration.",
            },
        ]

        for document in documents:
            print(f"{document['id']} — {document['title']} — page {document['page']}")
        '''),
        md('''
        ## 4. Pourquoi découper les documents ?

        Un PDF peut contenir des centaines de pages. Envoyer tout le PDF au modèle serait lent, coûteux et souvent impossible à cause de la taille maximale du contexte.

        On le découpe donc en **chunks**, c'est-à-dire en petits passages. Un léger chevauchement évite de couper une idée importante exactement entre deux chunks.
        '''),
        md('''
        ![Le chunking et les embeddings expliqués visuellement](assets/chunking_embeddings.png)
        '''),
        code('''
        def chunk_words(text: str, size: int = 10, overlap: int = 3) -> list[str]:
            words = text.split()
            step = max(1, size - overlap)
            return [" ".join(words[start:start + size]) for start in range(0, len(words), step)]

        example = (
            "Un document très long doit être découpé en passages plus petits "
            "afin de retrouver seulement les informations utiles à la question."
        )
        chunk_words(example)
        '''),
        md('''
        ### Comment choisir la taille d'un chunk ?

        Il n'existe pas de taille parfaite :

        - trop petit : le passage perd son contexte ;
        - trop grand : le passage mélange plusieurs sujets ;
        - bon compromis : une idée juridique cohérente, avec ses métadonnées.

        Dans le projet final, nous comparerons plusieurs tailles au lieu d'en choisir une au hasard.
        '''),
        md('''
        ## 5. Embeddings : représenter le sens avec des nombres

        Un embedding est une liste de nombres représentant approximativement le sens d'un texte. Deux passages qui parlent de concepts proches ont généralement des vecteurs proches.

        Exemple conceptuel :

        - « délai de traitement » et « combien de jours faut-il attendre ? » doivent être proches ;
        - « copie du justificatif » et « météo de demain » doivent être éloignés.

        Nous commençons avec un petit TF-IDF écrit en Python standard pour voir le mécanisme sans télécharger de modèle lourd. Plus tard, `multilingual-e5-base` permettra une vraie recherche sémantique multilingue.
        '''),
        code('''
        import math
        import re
        from collections import Counter

        def tokenize(text: str) -> list[str]:
            return re.findall(r"\\w+", text.lower(), flags=re.UNICODE)

        tokenized_documents = [tokenize(document["text"]) for document in documents]
        vocabulary = sorted({token for tokens in tokenized_documents for token in tokens})
        document_count = len(tokenized_documents)
        document_frequency = {
            term: sum(term in tokens for tokens in tokenized_documents)
            for term in vocabulary
        }
        idf = {
            term: math.log((1 + document_count) / (1 + document_frequency[term])) + 1
            for term in vocabulary
        }

        def tfidf_vector(text: str) -> list[float]:
            counts = Counter(tokenize(text))
            total = max(1, sum(counts.values()))
            return [(counts[term] / total) * idf.get(term, 0.0) for term in vocabulary]

        document_vectors = [tfidf_vector(document["text"]) for document in documents]
        print("Documents :", len(document_vectors))
        print("Dimensions du vocabulaire :", len(vocabulary))
        '''),
        md('''
        ## 6. Retrieval : retrouver les bons passages

        Nous transformons la question avec le même vectoriseur, puis calculons la similarité cosinus. Un score élevé signifie que la question et le passage sont proches dans cet espace.
        '''),
        code('''
        def cosine(left: list[float], right: list[float]) -> float:
            dot = sum(a * b for a, b in zip(left, right))
            left_norm = math.sqrt(sum(value * value for value in left))
            right_norm = math.sqrt(sum(value * value for value in right))
            if left_norm == 0 or right_norm == 0:
                return 0.0
            return dot / (left_norm * right_norm)

        def retrieve_tfidf(question: str, k: int = 2) -> list[dict]:
            query_vector = tfidf_vector(question)
            scores = [cosine(query_vector, vector) for vector in document_vectors]
            best_indices = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:k]
            return [
                {**documents[index], "score": float(scores[index])}
                for index in best_indices
            ]

        question = "Quel est le délai de traitement ?"
        results = retrieve_tfidf(question)
        [(result["id"], round(result["score"], 3), result["text"]) for result in results]
        '''),
        md('''
        ### Dense, lexical ou hybride ?

        - **Recherche lexicale (BM25/TF-IDF)** : excellente pour les mots exacts, numéros d'articles et expressions rares.
        - **Recherche dense (embeddings)** : meilleure pour les synonymes, reformulations et questions multilingues.
        - **Recherche hybride** : combine les deux ; c'est généralement notre choix pour les documents juridiques.
        '''),
        md('''
        ## 7. Construire le contexte et les citations

        Le modèle ne doit pas recevoir uniquement le texte. Il faut aussi transmettre l'identifiant du document et la page pour générer des citations vérifiables.
        '''),
        code('''
        def format_context(results: list[dict]) -> str:
            return "\\n\\n".join(
                f"[Source {item['id']}, page {item['page']}]\\n{item['text']}"
                for item in results
            )

        context = format_context(results)
        print(context)
        '''),
        md('''
        ## 8. Prompt contraint par les sources

        Le prompt définit les règles du modèle. Pour limiter les hallucinations, il lui demande :

        - d'utiliser uniquement les extraits fournis ;
        - de citer ses affirmations ;
        - de signaler quand les informations sont insuffisantes ;
        - de ne jamais présenter la réponse comme un avis juridique.
        '''),
        code('''
        def build_prompt(question: str, context: str, language: str = "français") -> str:
            parts = [
                "Tu es un assistant de recherche documentaire.",
                f"Réponds en {language} uniquement à partir des sources fournies.",
                "Ajoute une citation [Source ID, page N] après chaque affirmation importante.",
                "Si les sources ne permettent pas de répondre, indique-le clairement.",
                "Ne fournis pas d'avis juridique professionnel.",
                f"QUESTION : {question}",
                f"SOURCES :\\n{context}",
            ]
            return "\\n\\n".join(parts)

        prompt = build_prompt(question, context)
        print(prompt)
        '''),
        md('''
        ## 9. Un mini-RAG sans LLM

        Avant de connecter un modèle génératif, on peut déjà créer une réponse extractive. Cette étape permet de tester le retrieval et les citations indépendamment du LLM.
        '''),
        code('''
        def extractive_answer(question: str, threshold: float = 0.05) -> str:
            retrieved = retrieve_tfidf(question, k=2)
            useful = [item for item in retrieved if item["score"] >= threshold]
            if not useful:
                return "Les documents disponibles ne permettent pas de répondre à cette question."
            lines = [
                f"- {item['text']} [Source {item['id']}, page {item['page']}]"
                for item in useful
            ]
            return "Passages trouvés :\\n" + "\\n".join(lines)

        print(extractive_answer("Combien de jours faut-il attendre ?"))
        '''),
        md('''
        ## 10. Pourquoi le multilingue est plus difficile ?

        La même question peut apparaître sous différentes formes :

        - français : « Quel est le délai ? » ;
        - arabe : « ما هي مدة المعالجة؟ » ;
        - darija : « شحال خاصني نتسنى؟ ».

        TF-IDF ne comprend pas naturellement que ces phrases ont un sens proche. Un modèle d'embeddings multilingue projette leurs significations dans le même espace vectoriel.
        '''),
        code('''
        # Cellule optionnelle : elle télécharge le modèle lors de la première exécution.
        # from sentence_transformers import SentenceTransformer
        # multilingual_encoder = SentenceTransformer("intfloat/multilingual-e5-base")
        # examples = [
        #     "query: Quel est le délai ?",
        #     "query: ما هي مدة المعالجة؟",
        #     "query: شحال خاصني نتسنى؟",
        # ]
        # vectors = multilingual_encoder.encode(examples, normalize_embeddings=True)
        # vectors @ vectors.T
        '''),
        md('''
        ## 11. Évaluer un RAG

        Une belle réponse ne prouve pas que le système fonctionne. Il faut mesurer au moins deux parties séparément.

        ### Retrieval

        - `Recall@K` : le bon document apparaît-il parmi les K premiers ?
        - `MRR` : à quelle position apparaît le premier bon document ?

        ### Génération

        - fidélité : la réponse est-elle soutenue par les sources ?
        - exactitude des citations : document et page sont-ils corrects ?
        - complétude : la réponse couvre-t-elle les éléments utiles ?
        - abstention : refuse-t-elle correctement lorsque la preuve manque ?
        '''),
        code('''
        test_questions = [
            {"question": "Quel est le délai ?", "expected": "DOC-B"},
            {"question": "Comment corriger une erreur ?", "expected": "DOC-C"},
            {"question": "Où déposer la demande ?", "expected": "DOC-D"},
        ]

        correct = 0
        for test in test_questions:
            top_document = retrieve_tfidf(test["question"], k=1)[0]["id"]
            is_correct = top_document == test["expected"]
            correct += int(is_correct)
            print(test["question"], "→", top_document, "✓" if is_correct else "✗")

        print("Accuracy@1 pédagogique :", correct / len(test_questions))
        '''),
        md('''
        ## 12. Erreurs fréquentes à éviter

        1. indexer des documents sans conserver leur provenance ;
        2. utiliser des chunks trop grands ou trop petits sans évaluation ;
        3. mesurer uniquement la qualité du texte généré ;
        4. laisser le modèle répondre lorsque les sources sont insuffisantes ;
        5. mélanger des versions anciennes et actuelles d'un texte ;
        6. afficher une citation qui ne soutient pas réellement l'affirmation ;
        7. considérer le RAG comme un remplacement d'un professionnel du droit.
        '''),
        md('''
        ## 13. Exercices

        **Niveau 1** — Ajoute un cinquième document fictif puis vérifie qu'il peut être retrouvé.

        **Niveau 2** — Modifie `k` et observe comment les résultats changent.

        **Niveau 3** — Remplace TF-IDF par `multilingual-e5-base` et compare les trois langues.

        **Niveau 4** — Ajoute BM25 et fusionne le score lexical avec le score dense.

        **Niveau 5** — Branche un LLM local, impose les citations et crée des tests d'abstention.
        '''),
        md('''
        ## 14. Résumé final

        Un RAG est composé de deux grandes phases :

        - **indexation** : préparer les documents, créer les chunks et calculer les embeddings ;
        - **question-réponse** : retrouver les bons chunks, construire le prompt et générer une réponse citée.

        La qualité finale dépend souvent davantage du corpus, des métadonnées, du chunking et du retrieval que du choix du plus grand LLM.

        **Prochaine étape dans ce dépôt :** appliquer exactement ce pipeline à un corpus de documents juridiques marocains officiels, avec évaluation en français, arabe et darija.
        '''),
    ])

    print(f"Generated 9 notebooks in {NOTEBOOKS}")


if __name__ == "__main__":
    main()
