# Audit de l'existant

Inspection statique du 31 octobre 2026, branche locale `scout`, dernier commit
observé `f3ee372`. Le travail courant comporte de nombreuses modifications et
plusieurs suppressions de parsers officiels ; ces changements sont préexistants
à cette documentation. Les constats portent sur les fichiers de travail lus,
pas uniquement sur le commit.

## Ce qui existe

| Zone | Observation |
| --- | --- |
| Environnement | Python 3.12 dans `.python-version`, `pyproject.toml` et `uv.lock` |
| Schémas | Modèles Pydantic dans `core/schema/`, dont `VisionEntity` |
| Ingestion | `ScoutAgent` appelle `MainParser`, encode puis écrit dans Qdrant |
| Sources | `official/` pour Data Dragon et Riot live ; `community/` et `analytics/` pour les sources tierces |
| Cache | `data/cache.py`, cache mémoire avec expiration, pas un stockage persistant |
| Recherche | `RAGAgent`, recherche Qdrant, reranking par similarité et assemblage textuel |
| Démo | `main.py` collecte Ahri puis interroge `nexusmind_champions` via un client Qdrant partagé sur localhost:6333 |
| Git | Branches locales `main`, `develop`, `scout`, `parser`, `schema` ; `dev` non observée |

LangChain, LangGraph et Streamlit sont déclarés, mais aucun graphe LangGraph,
agent Coach LLM ou interface opérationnelle n'a été observé dans les fichiers
suivis inspectés. Aucun test automatisé, workflow CI ou manifeste de déploiement
n'a été trouvé dans les fichiers suivis. La présence de données Qdrant locales
ne constitue pas un test de qualité du RAG.

## Constats prioritaires

| Priorité | Constat vérifiable | Conséquence / action |
| --- | --- | --- |
| P0 | Scout et RAG importent `sentence_transformers`, absent des dépendances directes | Déclarer `sentence-transformers`, vérifier les autres imports directs dont NumPy, régénérer le lock et tester une installation propre |
| P0 | Git suit `core/schema/champion.py`, tandis que les imports utilisent `core.schema.Champion` | Risque d'échec sur Linux ; normaliser la casse dans une modification dédiée et tester les imports sous Linux |
| P0 | Les encodeurs retournent un vecteur nul si le modèle ne charge pas | Échec masqué ; interdire indexation/recherche dans cet état et retourner une erreur explicite |
| P0 | `MainParser` instancie et appelle Wiki, LoLalytics et Leaguepedia | Le mode Riot uniquement n'est pas implémenté ; isoler les fournisseurs puis supprimer les appels tiers du parcours par défaut |
| P1 | `RiotStaticParser` fixe `14.1.1` et `en_US` par défaut | Version et langue à rendre explicites, traçables et reproductibles |
| P1 | `riot_live_parser.py` utilise le même domaine plateforme pour Match-v5 et Spectator | Séparer routages régional et plateforme, revoir l'identification Riot ID/PUUID selon les API actuelles |
| P1 | `RAGAgent.search()` transmet le nom reçu sans résoudre ses alias ; les helpers passent `champions`, etc. | Incohérence avec les collections `nexusmind_*` ; centraliser et tester le mapping |
| P1 | `_build_filters()` emploie `MatchValue(any=value)` pour une liste | Vérifier le contrat Qdrant et utiliser le type de filtre approprié avec tests |
| P1 | `_extract_content()` réduit un champion essentiellement au nom/titre/résumé | Les sorts recherchés peuvent ne pas atteindre la réponse ; revoir documents et chunks |
| P1 | `_construct_answer()` assemble du texte, sans appel de LLM | La réponse actuelle n'est pas celle d'un coach expert ; isoler puis ajouter la génération |
| P1 | Le payload champion indique `source: scout_agent` | Perte de provenance réelle ; conserver URL/endpoint, patch et langue |
| P1 | Des valeurs de jeu sont initialisées par défaut ; le matchup peut valoir 50 % par défaut | Risque de présenter une valeur fictive comme observation ; expliciter absence, calcul ou hypothèse |
| P1 | Les requêtes Riot statiques et plusieurs appels live n'ont pas de timeout explicite | Ajouter délais, gestion des erreurs et quotas testables |
| P2 | Appels `requests` synchrones depuis des parcours `async` | Le mot-clé `async` ne garantit pas la concurrence ; isoler l'I/O ou adopter un client adapté après mesure |
| P2 | `.gitignore` ne couvre pas volumes Qdrant et logs ; ils sont non suivis localement | Compléter les exclusions dans un chantier dédié sans effacer les données |

`VisionEntity` décrit un modèle souhaité, sans preuve qu'un endpoint fournisse
position, durée et rayon pour chaque ward. Ne pas créer un scraper ou des valeurs
inventées simplement pour remplir tous les champs.

## Documentation historique et vérifications

L'ancien README évoquait CrewAI, Chroma/FAISS et un `requirements.txt` absent.
Le README des parsers mentionnait des chemins et capacités non conformes aux
fichiers actuels. Ils sont réalignés avec cet audit. `AUDIT_SCHEMA.md`, document
local préexistant non suivi lors de l'inspection, reste une note historique non
validée ; il ne remplace pas ce diagnostic.

Cette inspection n'a lancé ni collecte, ni modèle, ni requête Qdrant, ni suite
applicative. Le lanceur `python` du système n'était pas exécutable ; `uv` était
présent. Les corrections ci-dessus restent à implémenter et à tester. Aucun
paramètre distant GitHub (branche par défaut, rulesets, secrets) n'a été vérifié.

## Suite de l'audit — chantier Scout du 31 octobre 2026

Les constats précédents décrivent l'état historique et ne sont pas effacés.
Le nouveau package maintenu `src/nexusmind/` ne dépend pas des anciens parsers
ou schémas. Il déclare l'encodeur, fixe modèle/révision, rejette les vecteurs
invalides, conserve la provenance et utilise des noms de modules portables.
Le parcours officiel est `nexusmind ingest`, avec quatre catégories Riot,
archives JSON, catalogue SQLite et Qdrant ; voir le [guide](ingestion.md).

Une installation isolée a révélé en plus un conflit Qdrant/protobuf, corrigé
par dépendance client récente et contrainte protobuf explicite. Le lock évite
également la version grpcio retirée détectée pendant l'installation. Les tests
hors ligne couvrent normalisation, transport, erreurs de modèle, rejeu et
roundtrip Qdrant mémoire. Les tests ne valident pas un serveur distant ni la
qualité pédagogique du futur Coach. Les défauts dans les anciens fichiers
restent présents ; aucune modification utilisateur locale n'est embarquée.
