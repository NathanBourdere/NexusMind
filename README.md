# NexusMind — Coach League of Legends

Projet personnel de Nathan BOURDERE ANDREOU pour apprendre le RAG,
l'orchestration multi-agents et le déploiement à travers un coach LoL capable
d'expliquer la macro et la micro du jeu.

## État actuel

Le dépôt contient un Scout de collecte/indexation, des parsers, des modèles
Pydantic et un agent de recherche Qdrant. `main.py` illustre une collecte d'Ahri
puis une recherche. La réponse est aujourd'hui un assemblage textuel ; le Coach
LLM, le graphe d'orchestration et le déploiement restent à réaliser.

Le premier périmètre visé est un RAG fondé sur les données Riot, avec des
réponses sourcées et une abstention lorsque le corpus ne suffit pas. Le code
appelle encore des sources tierces : leur isolation est un chantier identifié.
Les données Riot seules ne constituent pas un manuel exhaustif de coaching.

## Démarrer

Python 3.12, uv et Qdrant sont les bases actuelles. Le projet possède un
`pyproject.toml` et un `uv.lock`, sans `requirements.txt`.

Lire le [guide local](docs/development.md) avant de lancer la démo : il indique
les prérequis manquants et les appels réseau/écritures effectués. L'installation
et la démo ne sont pas annoncées comme validées en environnement propre.

## Contribuer et apprendre

- [AGENTS.md](AGENTS.md) : instructions pour les agents et liens vers toutes les règles.
- [Documentation](docs/README.md) : index complet.
- [Audit](docs/audit.md) : état vérifié et défauts à corriger.
- [Architecture](docs/architecture.md) et [sources](docs/data-sources.md) : existant, cible et limites.
- [Git/GitHub](docs/git-workflow.md) : branches, commits atomiques et PR.
- [TDD et évaluation](docs/testing.md) : tests hors ligne et mesure du RAG.
- [Déploiement](docs/deployment.md) et [roadmap](docs/roadmap.md) : progression jusqu'à une release reproductible.

La branche d'intégration `dev` est initialisée depuis l'historique committé de
`scout`, qui contient celui de `develop`. Les branches historiques sont conservées ;
les protections GitHub restent à configurer séparément.
