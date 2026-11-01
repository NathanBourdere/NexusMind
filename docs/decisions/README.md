# Décisions d'architecture

Créer un ADR pour un changement de sources, responsabilités d'agents, schéma
d'indexation, modèle d'embedding, stratégie de déploiement ou seuils d'évaluation.
Les changements mineurs restent dans la PR.

- [0001 — Corpus Riot et pipeline simple](0001-riot-first.md)
- [0002 — Stockage, retrieval et orchestration pédagogique](0002-rag-orchestration.md)
- [0003 — Package Python installé et adaptateurs explicites](0003-python-package-layout.md)
- [0004 — Retrieval explicite et évaluation versionnée](0004-retrieval-baseline.md)
- [0005 — Coach injectable avec Gemini gratuit](0005-free-tier-coach.md)
- [0006 — Profil Coach rapide avec Flash-Lite](0006-low-latency-coach.md)
- [0007 — Interface locale et runtime persistant](0007-local-coach-interface.md)
- [0008 — Analyse après partie déterministe](0008-postgame-analysis.md)
- [0009 — Enrichissement explicite après le POC](0009-knowledge-sources.md)

Nommage : `NNNN-sujet-en-kebab-case.md`. Statuts : proposé, accepté, remplacé.
Une décision acceptée peut définir une cible encore non implémentée. Pour la
remplacer, ajouter un ADR lié plutôt que supprimer sa justification.

```markdown
# NNNN — Titre

Date : AAAA-MM-JJ
Statut : proposé

## Contexte

Problème, contraintes et preuves.

## Décision

Choix précis et périmètre.

## Conséquences

Bénéfices, limites, migration et validation.

## Options examinées

Alternatives et raison du choix.
```
