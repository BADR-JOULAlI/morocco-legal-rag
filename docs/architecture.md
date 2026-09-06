# Architecture initiale

1. **Collecte** : récupération contrôlée de documents juridiques publics et conservation des métadonnées.
2. **Prétraitement** : extraction du texte, OCR si nécessaire, normalisation arabe et découpage avec contexte.
3. **Indexation** : embeddings multilingues, index vectoriel et index lexical.
4. **Récupération** : recherche hybride, reranking et filtrage par type de document/date.
5. **Génération** : réponse contrainte par le contexte récupéré, dans la langue demandée.
6. **Traçabilité** : chaque affirmation doit renvoyer à un document et, si possible, à une page.
7. **Évaluation** : recall@k, précision des citations, faithfulness et questions de test multilingues.
