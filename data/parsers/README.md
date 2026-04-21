# NexusMind : Parsers Engine

Ce module constitue le moteur **ETL (Extract, Transform, Load)** de l'écosystème NexusMind. Son rôle est de transformer des flux de données hétérogènes (API Riot, Scraping Wiki, Analytics) en objets Python typés via **Pydantic**, tout en garantissant la traçabilité des sources pour l'Agent LLM.

---

## Architecture du Dossier `parsers/`

Le dossier est structuré par domaine de provenance pour faciliter la maintenance et le sourcing des données.

```text
parsers/
├── main_parser.py           # Chef d'orchestre : fusionne et source les données
├── riot/
│   ├── static_parser.py     # Data Dragon : Stats de base, Items, Runes
│   └── live_parser.py       # Spectator v5 & Live Client : État de la game en temps réel
├── community/
│   ├── wiki_parser.py       # Fandom Wiki : Timers de jungle, interactions cachées
│   └── cdragon_parser.py    # CommunityDragon : Données bas-niveau (binaires) et assets
└── analytics/
    ├── lolalytics_parser.py # Meta data : Winrates, Power spikes, Tier lists
    └── opgg_parser.py       # Profiling : Historique et psychologie du joueur
```

## 🛰️ Sources de Données & Traçabilité

Chaque donnée extraite est accompagnée d'un tag de provenance. Cela permet à l'Agent LLM de citer ses sources dans ses conseils (ex: *"D'après LoLalytics, ce build a un winrate de..."*).

| Source | Type de Données | Utilisation |
| :--- | :--- | :--- |
| **Riot Data Dragon** | Statique | Base de référence pour les champions, sorts et items. |
| **Riot Live API** | Dynamique | Positions (X,Y), PV, Golds, Inventaires et Événements de jeu. |
| **WikiLoL (Fandom)** | Expertise | Frame data, priorités d'animations et mécaniques de niche. |
| **CommunityDragon** | Raw Data | Tooltips complexes et données non-documentées par Riot. |
| **LoLalytics** | Analytique | Probabilités de victoire par matchup et efficacité des builds. |
| **Leaguepedia** | Pro-Meta | Tendances de la scène compétitive (LCK, LEC, LPL). |

## 🚀 Flux de Travail (Pipeline)

Le `main_parser` orchestre la récupération des données via un pipeline asynchrone :

1.  **Extraction** : Le `main_parser` appelle les différents sous-parsers (Riot, Wiki, Analytics) de manière asynchrone pour minimiser la latence.
2.  **Transformation** : Les données brutes sont nettoyées et mappées vers nos classes définies dans `core/schema/`.
3.  **Enrichissement** : Les métadonnées analytiques et les mécaniques de niche sont injectées dans le champ `metadata` des objets (ex: `Champion.metadata`).
4.  **Sourcing** : Un dictionnaire d'attribution est généré pour chaque `GameStateSnapshot`, liant chaque information à sa source d'origine.
5.  **Chargement** : Les objets finaux enrichis sont envoyés à la base vectorielle (RAG/Qdrant) ou directement à l'Agent LLM pour analyse.

## 🛠️ Installation & Usage

### Pré-requis

* **Python 3.12**
* **Clé API Riot Games** (RGAPI) valide.