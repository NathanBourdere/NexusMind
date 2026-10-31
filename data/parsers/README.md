# Parsers NexusMind

Ce dossier est désormais historique. Le parcours maintenu est dans
`src/nexusmind/` : voir le [guide d'ingestion](../../docs/ingestion.md) et
l'[ADR-0003](../../docs/decisions/0003-python-package-layout.md). Il n'importe pas
ces parsers ni les sources tierces. Les descriptions ci-dessous concernent
l'ancienne implémentation, conservée pour migration.

Les parsers transforment des réponses externes en objets métier Pydantic.
Ils ne doivent pas décider du conseil pédagogique ni écrire directement dans
Qdrant : ces rôles appartiennent à Scout et au futur Coach.

## Arborescence actuelle

```text
data/parsers/
  main_parser.py
  official/
    riot_static_parser.py
    riot_live_parser.py
  community/
    wiki_parser.py
    cdragon_parser.py
  analytics/
    lolalytics_parser.py
    leaguepedia_parser.py
```

`MainParser` instancie et utilise Data Dragon, Riot live, Wiki, LoLalytics et
Leaguepedia. La présence de `cdragon_parser.py` ne prouve pas son intégration
dans ce parcours. Les requêtes HTTP actuelles sont synchrones, même lorsqu'elles
sont appelées depuis une méthode `async`.

Le périmètre cible est Riot uniquement. Ce mode n'est pas encore implémenté.
Spectator ne fournit pas à lui seul un état complet avec toutes les positions,
PV et inventaires ; ne pas présenter les valeurs par défaut du modèle comme
de la télémétrie observée.

Lire les [instructions du dépôt](../../AGENTS.md),
l'[audit](../../docs/audit.md), les [sources et contrats](../../docs/data-sources.md)
et les [tests](../../docs/testing.md) avant toute évolution de parser.
Préserver la provenance réelle, le patch et la langue ; représenter les champs
non disponibles explicitement et tester avec des fixtures sans réseau.
