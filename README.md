# Morocco Legal RAG

Assistant de recherche juridique multilingue pour des documents publics marocains.

Le système permet de poser une question en français, arabe ou darija et d'obtenir une réponse fondée sur les documents indexés, avec les sources citées. Il ne remplace pas un professionnel du droit.

## Objectifs

- ingestion de lois, décrets et documents juridiques publics ;
- recherche hybride sémantique et lexicale ;
- réponses en français, arabe et darija ;
- citations vérifiables avec page et document source ;
- évaluation de la récupération et de la fidélité des réponses ;
- API et interface de démonstration.

## Stack

Python, FastAPI, Gradio, embeddings multilingues Hugging Face, BM25, fusion RRF, Docker et Qdrant comme stockage vectoriel prévu.

## Ce qui fonctionne déjà

- catalogue auditable de sources officielles ;
- téléchargement limité à une liste de domaines autorisés ;
- extraction PDF page par page avec hash SHA-256 ;
- détection des pages nécessitant un OCR ;
- chunking conservant la provenance ;
- recherche hybride dense + BM25 avec fusion RRF ;
- génération extractive sûre et adaptateur LLM compatible OpenAI ;
- citations contenant le document, la page, l'extrait et l'URL ;
- API FastAPI et interface Gradio ;
- métriques Recall@K, MRR et nDCG ;
- tests, Docker et intégration continue.

## Parcours notebook-first

Le projet est organisé comme un laboratoire reproductible :

1. cadrage et exploration des sources ;
2. collecte contrôlée des documents ;
3. extraction PDF et OCR ;
4. nettoyage, normalisation et découpage ;
5. indexation hybride dense + BM25 ;
6. génération multilingue avec citations ;
7. évaluation du retrieval et des réponses ;
8. démonstration interactive.

Pour débuter, ouvrir d'abord `notebooks/08_rag_beginner_course.ipynb`. Ce cours autonome explique les concepts avec trois infographies et un mini-RAG exécutable sans modèle lourd.

Les notebooks sont générés de façon reproductible par `tools/build_notebooks.py`.

## Démarrage

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,ml,notebooks,ocr,ui]"
python tools/build_notebooks.py
jupyter lab
```

Pour lancer seulement l'API avec les dépendances minimales :

```powershell
pip install -e ".[dev]"
uvicorn morocco_legal_rag.api:app --reload
```

L'API expose :

- `GET /health` ;
- `POST /ask` ;
- documentation interactive sur `http://localhost:8000/docs`.
- interface web sur `http://localhost:8000/`.

Pour télécharger uniquement les entrées approuvées du catalogue :

```powershell
python scripts/download_official_sources.py
python scripts/ingest_downloaded_pdfs.py
```

Pour lancer l'interface après l'API :

```powershell
morocco-legal-ui
```

## Statut

MVP local en cours de validation. Les fichiers bruts, indexes et résultats d'OCR restent exclus de Git.

## Avertissement

Ce projet est destiné à la recherche et à la démonstration technique. Les réponses doivent être vérifiées dans les textes officiels et ne constituent pas un avis juridique.
