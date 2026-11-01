# Exécuter l'ingestion Scout

Ce guide décrit Data Dragon. L'extension CommunityDragon, guide Riot et import
attribué utilise `collect-knowledge` puis `ingest-knowledge` : voir le
[guide d'enrichissement](knowledge-sources.md). Elle ne réactive pas les anciens
parsers et ne change pas les sources de `nexusmind ingest`.

## Installation

Depuis la racine du checkout à utiliser, Python 3.12 et uv :

```powershell
rtk proxy uv sync --frozen
rtk proxy uv run --frozen nexusmind --help
```

Le package installé vient de `src/nexusmind/`. Les dépendances de test sont dans
le groupe `dev`, installé par défaut par uv. Les intégrations historiques sont
optionnelles (`--extra legacy`) et ne font pas partie du parcours supporté.
LangGraph est réservé à l'extra `orchestration` ; aucun LLM n'intervient ici.

Le modèle multilingue `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
est fixé à la révision `86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d`. Le premier
chargement peut télécharger ses poids depuis Hugging Face. `--offline-model`
interdit ce téléchargement et exige que cette révision soit déjà en cache.
`--model-cache CHEMIN` choisit un cache explicite. Aucun modèle n'est chargé à l'import.
L'inférence utilise le CPU avec quatre threads pour borner sa consommation locale.

## Premier lot puis corpus complet

```powershell
rtk proxy uv run --frozen nexusmind ingest --champion Ahri --kind champion
rtk proxy uv run --frozen nexusmind status
rtk proxy uv run --frozen nexusmind ingest --patch 16.21.1 --locale fr_FR
```

Sans `--patch`, Scout résout une fois la version Data Dragon publiée puis la
réutilise pour tout le lot. `16.21.1` est un exemple de version testée, pas une
promesse qu'elle reste la plus récente. Sans `--kind`, les quatre catégories sont
collectées : tous les champions (détail, passif et sorts), objets, runes et sorts
d'invocateur. `--champion` peut être répété ; il limite les champions, pas les
autres catégories. Combiner avec `--kind champion` pour un lot uniquement champion.

Data Dragon est public et ne nécessite pas de clé Riot. Ce parcours n'appelle
ni Wiki, ni LoLalytics, ni Leaguepedia, ni les API de données joueur. Les notes
de patch, Match-v5, live et Coach restent des extensions futures.

Les documents sont découpés par section, puis en fragments de 400 caractères si
nécessaire. Ils gardent source, patch, langue et identité d'entité. L'encodeur
normalise les vecteurs et refuse les textes dépassant 512 tokens plutôt que de
les tronquer silencieusement. Les vecteurs nuls, non finis ou de dimension
incorrecte sont rejetés avant écriture.

## Stockages et rapports

```text
.runtime/
  raw/                 # archives JSON dédupliquées par URL et contenu
  catalog.sqlite       # passages normalisés et journal des exécutions
  qdrant/              # index Qdrant embarqué persistant
```

Tout reste local et ignoré par Git. `--data-dir CHEMIN` sélectionne cet ensemble
de stockages ; répéter la même option pour `ingest`, `search` et `status`.
Une seule commande à la fois doit ouvrir le même stockage Qdrant embarqué.
Le mode embarqué suffit au développement ; plusieurs processus doivent utiliser
un serveur Qdrant et `--qdrant-url http://localhost:6333` (ou la variable
`NEXUSMIND_QDRANT_URL`). Le serveur doit être lancé séparément. Aucun `.env`
n'est chargé implicitement. La CLI possède et ferme ses clients.
Une panne pendant l'initialisation du modèle ou l'ouverture des clients peut
précéder la création du journal : elle reste signalée par code non nul et stderr.

La collection `nexusmind_knowledge_v1_<empreinte>` est spécifique à l'encodeur,
à sa révision et au format. Aucun effacement ou remplacement de collection
historique. Le rejeu du même lot réutilise les identifiants et archives sans
doublons. Cette propriété suppose un contenu identique ; la suppression de
passages retirés par Riot nécessite une future stratégie de snapshot/migration.

Le JSON final contient `run_id`, `status`, `patch`, `locale`, `collection`,
nombre de ressources et passages écrits, dates et erreur éventuelle. `status`
lit le dernier journal sans charger le modèle. La commande retourne un code
non nul si une source, l'encodeur ou le stockage échoue. Des lots déjà écrits
peuvent subsister après un échec : le journal indique `failed`, jamais un succès
complet. Relancer après correction réconcilie les stockages ; aucune atomicité
distribuée entre SQLite et Qdrant n'est annoncée.

## Vérifier les passages indexés

```powershell
rtk proxy uv run --frozen nexusmind search "Quels sont les sorts de Ahri ?" --patch 16.21.1
```

Utiliser le patch du rapport d'ingestion. Les résultats sont filtrés par patch
et locale et contiennent texte, source et score. Un score de similarité n'est
pas une confiance de vérité. Une collection absente est une erreur ; une
recherche sans passage renvoie une liste vide. Ce contrôle ne mesure pas encore
la qualité globale du RAG et ne génère pas de réponse de coaching.
Pour des preuves structurées avec filtrage d'entité, clarification et évaluation,
utiliser désormais le [parcours retrieval](retrieval.md) via `nexusmind retrieve`.

## Tests et contrôles

```powershell
rtk proxy uv run --frozen pytest -q
rtk proxy uv run --frozen ruff check src tests
rtk proxy uv run --frozen ruff format --check src tests
```

La suite utilise des doubles pour HTTP et embeddings, et Qdrant en mémoire pour
le contrat d'intégration. Aucun téléchargement de modèle ni accès Riot pendant
les tests. Le test avec un serveur Qdrant distant reste à exécuter séparément.
