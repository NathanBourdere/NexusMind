# Développement local

Python 3.12, uv et le lock du dépôt sont la référence. Le code maintenu est le
package installé `src/nexusmind/` ; la séparation des couches est définie dans
l'[architecture](architecture.md) et l'[ADR-0003](decisions/0003-python-package-layout.md).

## Installation et vérification

Depuis la racine du checkout :

```powershell
rtk proxy uv sync --frozen
rtk proxy uv run --frozen nexusmind --help
rtk proxy uv run --frozen pytest -q
rtk proxy uv run --frozen ruff check src tests
rtk proxy uv run --frozen ruff format --check src tests
rtk proxy uv build
```

Les exemples utilisent RTK selon l'instruction locale. Sans RTK, enlever le
préfixe `rtk proxy` et conserver la commande sous-jacente. `uv --directory CHEMIN`
permet de sélectionner explicitement un autre checkout ou worktree.

L'installation inclut les outils du groupe `dev`. PyTorch utilise l'index CPU
explicite sur Linux pour éviter les dépendances CUDA en CI. La contrainte protobuf
évite l'incompatibilité des anciens wrappers d'énumération avec le client Qdrant.
Les intégrations historiques et l'orchestration sont des extras optionnels ;
elles ne sont pas nécessaires pour ingérer Riot.

Voir le [guide Scout](ingestion.md) pour la collecte, le cache du modèle, les
stockages locaux et la recherche de contrôle. `main.py` reste une démo historique
non supportée ; les commandes maintenues sont `nexusmind` et `python -m nexusmind`.
Ne pas lancer la démo historique pour tester le nouveau parcours.

La commande `coach` utilise `GEMINI_API_KEY` injectée par environnement, sans
charger `.env`. La confirmation du projet gratuit, les bornes et les exemples
sont dans le [guide Coach](coach.md). Aucune clé n'est nécessaire aux tests.

## Organisation des changements

- Domaine : modèles et transformations sans SDK HTTP/ML/base de données.
- Application : cas d'usage et ports injectables, pas de dépendance sur les adaptateurs.
- Infrastructure : clients Riot, encodeur, SQLite et Qdrant, créés explicitement.
- CLI : configuration, construction des adaptateurs et fermeture des ressources.
- Tests : fixtures synthétiques, doubles HTTP/embeddings, Qdrant isolé en mémoire.
- `.runtime/` : données générées, jamais committées.

Ne pas modifier les dossiers historiques pour une nouvelle fonctionnalité.
Leur migration physique se fera après réconciliation du travail utilisateur.
Les classes historiques décrivant des états complets de jeu ne définissent pas
les champs réellement disponibles dans Data Dragon.

## Conventions

Typage des interfaces, erreurs explicites et validation aux frontières. Aucun
appel réseau à l'import, aucun vecteur nul de secours. Préserver la provenance,
les unités et les dates UTC avec fuseau. Un client partagé a un propriétaire
explicite ; toute ressource possédée est fermée même en cas d'échec.

Toute dépendance importée directement est déclarée ; une contrainte de
compatibilité transitive doit être expliquée. Modifier manifest et lock ensemble,
sans éditer le lock à la main. Définir les paramètres réellement pris en charge
dans le guide d'ingestion ; `.env` n'est pas chargé automatiquement.

Avant livraison : suite pertinente, lint/format, `git diff --check`, revue du
diff indexé et mise à jour des documents. Les tests d'intégration mémoire ne
valident pas un déploiement Qdrant distant ; signaler cette limite.
