# Feuille de route

Travail restant, pas fonctionnalités livrées. Chaque étape peut être découpée en
plusieurs PR atomiques avec tests. Conserver l'objectif d'apprentissage sans
cumuler toutes les inconnues dans une seule PR.

| Étape | Branche indicative | Résultat vérifiable |
| --- | --- | --- |
| 0. Organiser Git | `chore/git-workflow` | Inventaire des changements et branches ; migration `develop` vers `dev` revue ; protections après disponibilité des contrôles |
| 1a. Installation | `fix/runtime-dependencies` | Dépendances directes et lock cohérents ; installation Python 3.12 propre ; casse des imports vérifiée sous Linux |
| 1b. Socle TDD | `test/offline-foundation` | Pytest/asyncio, Ruff et fixtures ; premier test utile hors ligne et commandes documentées |
| 1c. CI | `chore/offline-ci` | Workflow vert sur Linux, sans secret ou API Riot ; noms réels des contrôles documentés |
| 2. Riot uniquement | `feat/riot-only-ingestion` | Aucun appel tiers ; version/langue explicites ; Data Dragon validé par fixtures ; délais et erreurs testés |
| 3a. Embeddings | `fix/embedding-failures` | Panne visible ; aucun vecteur nul de secours ; dimension vérifiée |
| 3b. Documents | `feat/versioned-documents` | Chunks traçables, patch/langue, identités stables, ingestion sans doublons |
| 3c. Retrieval | `fix/rag-contracts` | Alias et filtres corrigés ; vide distinct de panne ; roundtrip Qdrant isolé |
| 4. Baseline | `test/rag-evaluation` | Au moins 20 questions annotées, mesures reproductibles, cas d'abstention et seuils décidés |
| 5. Coach LLM | `feat/grounded-coach` | Fournisseur injecté, contexte borné, citations, abstention et exercice ; comparaison à la baseline |
| 6. Après partie | `feat/post-game-analysis` | Riot ID/PUUID, routage correct, Match-v5/timeline, mesures sourcées sans causalité inventée ; conservation définie |
| 7. Orchestration | `feat/langgraph-pipeline` | Graphe typé, transitions et budgets bornés, traces ; comparaison au pipeline simple |
| 8. Interface/staging | `feat/coach-interface` | Question et contexte joueur, sources/patch visibles, erreurs explicites, artefact et smoke test |
| 9. Release | `chore/release-pipeline` | Tag, notes, livraison traçable, restauration et rollback vérifiés |

Le live et les sources tierces ne conditionnent pas le MVP. Réexaminer une source
supplémentaire uniquement pour une lacune mesurée et un accès durable autorisé,
avec nouvel ADR.

Une tâche est terminée quand le comportement est démontré, les contrôles adaptés
passent, la documentation correspond au code et les limites restent explicites.
Une intégration indisponible n'est pas validée par les seuls tests unitaires.
