# 0001 — Corpus Riot et pipeline simple

Date : 2026-10-31
Statut : accepté comme direction du MVP, implémentation à réaliser

## Contexte

NexusMind sert à apprendre le RAG, l'orchestration multi-agents et le déploiement.
Les restrictions et abonnements compliquent la collecte multisource. Le propriétaire
souhaite revenir à Riot si l'accès aux autres sources ne peut être assuré.
L'inspection ne démontre pas d'accès tiers reproductible et confirme plusieurs
dépendances à ces sources.

## Décision

MVP fondé sur Data Dragon versionné, Qdrant et pipeline testable. Scout ingère,
RAG récupère les passages et Coach génère l'explication. Ajouter le Coach puis
LangGraph après une baseline de recherche mesurée. Notes de patch officielles
et Match-v5 sont des extensions explicites. Le MVP ne dépend ni du live ni du scraping.

## Conséquences

Collecte plus maîtrisable et responsabilités utiles pour apprendre le multi-agents.
Le corpus initial ne couvre pas toute la macro/micro : mesurer les lacunes,
s'abstenir et séparer conseils inférés et faits sourcés. Isoler les intégrations
tierces du parcours par défaut dans une PR dédiée ; cet ADR ne réalise pas le retrait.

Validation : tests hors ligne, aucun appel tiers, lot rejouable, provenance
visible et évaluation des questions couvertes comme des cas hors corpus.

## Options examinées

- Maintenir tous les scrapers : coût d'accès et de maintenance excessif pour le premier incrément.
- Graphe complexe immédiat : multiplie les inconnues avant les tests et mesures.
- Abandonner le multi-agents : inutile ; un pipeline simple sert de comparaison avant orchestration.
