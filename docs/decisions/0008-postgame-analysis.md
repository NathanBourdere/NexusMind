# 0008 — Analyste après partie déterministe et données en mémoire

Date : 2026-11-01
Statut : accepté

## Contexte

Le Coach statique ne peut pas analyser une partie. Le propriétaire demande un
premier coaching personnalisé à partir des données officielles, sans coût LLM
supplémentaire ni télémétrie live.

## Décision

Ajouter un port MatchSource injecté, un adaptateur Account-v1/Match-v5 et un
Analyste calculant les métriques par code. Exposer `analyze-match` sans chargement
ML et `/api/postgame` dans le chat local. Une demande collecte une partie et
sa timeline, avec quatre appels maximum, timeouts et erreurs typées.

Conserver `gameVersion`, source et date ; ne pas forcer un patch Data Dragon.
Préserver les absences et les ratios non définis. Comparer les lanes uniquement
si Riot fournit un rôle et un adversaire unique. Les conseils restent des
hypothèses, sans causalité déduite d'un événement suivant une mort.

Ne pas envoyer les données de partie au LLM, ne pas les indexer dans Qdrant,
ne pas conserver de réponses brutes. Une sauvegarde locale du rapport est
volontaire, sans PUUID ni identifiants des autres joueurs. Aucun identifiant
réel dans les fixtures ou la documentation publique.

## Conséquences

Les calculs sont reproductibles sans réseau. La clé Riot et ses quotas restent
nécessaires pour collecter réellement ; les clés de développement expirent.
Ce prototype n'inclut pas un historique longitudinal, une estimation de MMR,
une interprétation de replay ou une inférence de causalité. Le graphe LangGraph
reste un chantier ultérieur. Voir le [guide](../postgame.md).
