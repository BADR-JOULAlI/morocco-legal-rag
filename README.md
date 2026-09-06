# Morocco Legal RAG

Assistant de recherche juridique multilingue pour des documents publics marocains.

Le système permettra de poser une question en français, arabe ou darija et d'obtenir une réponse fondée sur les documents indexés, avec les sources citées. Il ne remplace pas un professionnel du droit.

## Objectifs

- ingestion de lois, décrets et documents juridiques publics ;
- recherche hybride sémantique et lexicale ;
- réponses en français, arabe et darija ;
- citations vérifiables avec page et document source ;
- évaluation de la récupération et de la fidélité des réponses ;
- API et interface de démonstration.

## Stack prévue

Python, FastAPI, Qdrant ou Chroma, modèles multilingues Hugging Face, PostgreSQL, Streamlit et Docker.

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

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -e .
python tools/build_notebooks.py
jupyter lab
```

## Statut

Structure notebook-first initialisée. La prochaine étape est d'ajouter exclusivement des sources juridiques officielles ou clairement identifiées.

## Avertissement

Ce projet est destiné à la recherche et à la démonstration technique. Les réponses doivent être vérifiées dans les textes officiels et ne constituent pas un avis juridique.
