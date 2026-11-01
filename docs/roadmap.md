# Feuille de route

Travail restant, pas fonctionnalités livrées. Chaque étape peut être découpée en
plusieurs PR atomiques avec tests. Conserver l'objectif d'apprentissage sans
cumuler toutes les inconnues dans une seule PR.

## Avancement du chantier Scout

Le package `src/nexusmind/` couvre désormais installation, normalisation Riot,
archives JSON, catalogue SQLite, vrais embeddings multilingues et index Qdrant
local. Les tests et Ruff sont disponibles ; le rejeu, les erreurs et les filtres
patch/langue sont couverts. Les dossiers historiques restent hors package.
Voir le [guide d'ingestion](ingestion.md) et l'[ADR-0003](decisions/0003-python-package-layout.md).
Les étapes ci-dessous restent le découpage de référence ; les alias de l'ancien
RAG, son reranking et ses schémas historiques ne sont pas corrigés par le nouveau Scout.

| Étape | Branche indicative | Résultat vérifiable |
| --- | --- | --- |
| 0. Organiser Git | `chore/git-workflow` | `dev` initialisée depuis `scout` après comparaison avec `develop` ; finaliser les cibles de PR et protections après disponibilité des contrôles |
| 1a. Installation | `feat/scout-ingestion` | Réalisée pour le package maintenu : installation Python 3.12 propre, dépendances et lock ; modules en snake_case |
| 1b. Socle TDD | `feat/scout-ingestion` | Réalisé : Pytest, Ruff, doubles injectés, tests de panne et roundtrip Qdrant mémoire |
| 1c. CI | `feat/scout-ingestion` | Workflow `CI` / job `python-checks` : premier passage Linux réussi ; chaque nouveau commit doit repasser les contrôles |
| 2. Riot uniquement | `feat/scout-ingestion` | Réalisé sur le parcours maintenu : quatre catégories statiques, version/langue explicites, délais et retries bornés |
| 3a. Embeddings | `feat/scout-ingestion` | Réalisé : modèle/révision fixés, vecteurs invalides rejetés, dimension et absence de troncature contrôlées |
| 3b. Documents | `feat/scout-ingestion` | Réalisé : JSON dédupliqués, passages/rapports SQLite, chunks traçables et identités stables ; suppression des anciens passages après changement de contenu à traiter |
| 3c. Retrieval | `feat/retrieval-baseline` | Réalisé dans le package maintenu : preuves structurées, filtres d'entité/section, ambiguïtés et pannes distinctes ; ancien RAG inchangé |
| 4. Baseline | `feat/retrieval-baseline` | 37 cas annotés et rapport avant/après publiés ; suite réduite non indépendante, aucun seuil général de qualité imposé |
| 5. Coach LLM | `feat/grounded-coach` | Fournisseur injecté, contexte borné, citations, abstention et exercice ; comparaison à la baseline |
| 6. Après partie | `feat/post-game-analysis` | Riot ID/PUUID, routage correct, Match-v5/timeline, mesures sourcées sans causalité inventée ; conservation définie |
| 7. Orchestration | `feat/langgraph-pipeline` | Graphe typé, transitions et budgets bornés, traces ; comparaison au pipeline simple |
| 8. Interface/staging | `feat/coach-interface` | Question et contexte joueur, sources/patch visibles, erreurs explicites, artefact et smoke test |
| 9. Release | `chore/release-pipeline` | Tag, notes, livraison traçable, restauration et rollback vérifiés |

Le live et les sources tierces ne conditionnent pas le MVP. Réexaminer une source
supplémentaire uniquement pour une lacune mesurée et un accès durable autorisé,
avec nouvel ADR.

L'[ADR-0002](decisions/0002-rag-orchestration.md) précise l'orchestration validée :
Scout et Retriever déterministes, Coach LLM, puis Analyste et vérificateur.
Le planificateur de progression vient après l'analyse de partie ; les spécialistes
patch et macro/micro restent optionnels selon les résultats de l'évaluation.

Une tâche est terminée quand le comportement est démontré, les contrôles adaptés
passent, la documentation correspond au code et les limites restent explicites.
Une intégration indisponible n'est pas validée par les seuls tests unitaires.
