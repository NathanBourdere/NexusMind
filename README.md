# NexusMind — Coach League of Legends

Projet personnel de Nathan BOURDERE ANDREOU pour apprendre le RAG,
l'orchestration multi-agents et le déploiement, appliqués à un coach LoL.

## Parcours disponible

Le Scout maintenu collecte les données publiques Riot Data Dragon : champions,
passifs, sorts, objets, runes et sorts d'invocateur. Il archive les réponses JSON,
produit des passages avec provenance/patch/langue, génère de vrais embeddings
multilingues et les indexe dans Qdrant. SQLite conserve passages et rapports.
Le rejeu d'un lot identique évite les doublons ; les échecs sont explicites.

Le retrieval retourne des preuves structurées, filtre les entités et demande
des précisions lorsqu'un nom est ambigu. Une baseline versionnée compare ses
résultats à la recherche brute sur 37 cas annotés. Le Coach Gemini est implémenté
avec citations et abstentions, testé hors ligne et sur un premier cas réel avec
Gemini 3.8 Flash, puis sur 37 cas avec Flash-Lite ; la revue humaine indépendante
reste à faire. Match-v5 et l'orchestration
LangGraph restent à développer. Les données Riot seules ne
constituent pas un corpus exhaustif de pédagogie macro/micro.

Le Coach utilise désormais Flash-Lite par défaut : cinq appels réels mesurés
entre 1,27 et 2,10 s, hors chargement initial et retrieval. Voir les
[mesures et limites](docs/validation/coach-latency-2026-11-01.md).

## Démarrer

Python 3.12 et uv, depuis la racine du dépôt :

```powershell
rtk proxy uv sync --frozen
rtk proxy uv run --frozen nexusmind ingest --champion Ahri --kind champion
rtk proxy uv run --frozen nexusmind status
```

Le premier chargement peut télécharger les poids du modèle. Aucune clé Riot,
aucun abonnement et aucun serveur Qdrant ne sont nécessaires au mode local.
Sans sélection de champion ou catégorie, `nexusmind ingest` collecte le corpus
statique complet. Les données sont écrites dans `.runtime/`, ignoré par Git.

Pour chercher, utiliser le patch du rapport :

```powershell
rtk proxy uv run --frozen nexusmind retrieve "Quels sont les sorts de Ahri ?" --patch 16.21.1
```

Le [guide d'ingestion](docs/ingestion.md) décrit les versions explicites,
catégories, options de stockage, serveur Qdrant et limites du rejeu.
Le [guide retrieval](docs/retrieval.md) décrit filtres, statuts, clarifications
et commande `evaluate`. Les [mesures](docs/validation/retrieval-2026-10-31.md)
portent sur un jeu limité de questions, sans valider le futur Coach.

Le [guide Coach](docs/coach.md) explique `nexusmind coach`, la clé Gemini, le
projet sans facturation et les limites. Le budget cible est zéro euro ; le code
ne peut pas vérifier l'état de facturation du compte fournisseur.

Pour utiliser le chat local, installer l'extra `web` puis lancer `nexusmind serve`.
Le [guide web](docs/web.md) donne la commande complète. L'encodeur reste chargé
pendant la session, avec réponses, sources et patch visibles dans le navigateur.

## Structure

```text
src/nexusmind/   # domaine, application Scout, infrastructure et CLI maintenus
tests/          # tests hors ligne et intégration Qdrant isolée
evaluation/     # annotations et rapport mesuré, sans corpus
docs/           # architecture, décisions et procédures
.github/        # CI, modèles d'issues et de PR
.runtime/       # archives, SQLite et Qdrant locaux (non versionnés)
```

Les anciens `agents/`, `core/`, `data/parsers/` et `main.py` sont conservés pour
migration et n'entrent pas dans le package maintenu. Ne pas utiliser `main.py`
comme point d'entrée de la nouvelle ingestion.

## Contribuer

- [AGENTS.md](AGENTS.md) et [index documentaire](docs/README.md).
- [Architecture](docs/architecture.md), [sources](docs/data-sources.md) et [décisions](docs/decisions/README.md).
- [Développement](docs/development.md), [TDD](docs/testing.md) et [Git/GitHub](docs/git-workflow.md).
- [Audit historique](docs/audit.md), [roadmap](docs/roadmap.md) et [déploiement](docs/deployment.md).
