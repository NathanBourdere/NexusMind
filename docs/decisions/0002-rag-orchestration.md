# 0002 — Séparer stockage, retrieval et orchestration pédagogique

Date : 2026-10-31
Statut : accepté par le propriétaire ; implémentation à réaliser

## Contexte

Après l'audit et l'ADR-0001, le propriétaire a validé une architecture RAG et
multi-agent progressive. Le projet doit préserver son objectif pédagogique
sans demander à des LLM d'effectuer des calculs ou collectes déterministes.

## Décision

Séparer ingestion hors requête et réponse au joueur. Conserver des JSON
versionnés pour la reproductibilité, SQLite pour les lookups et rapports,
et Qdrant pour les passages explicatifs. Une collection de connaissances par
génération compatible porte les filtres entité/patch/langue ; les données joueur
sont séparées. Aucun transfert des collections actuelles sans migration testée.

Commencer par Scout, Retriever et Coach. Scout et Retriever restent des services
Python déterministes, même si leurs noms historiques contiennent « Agent ».
Le Coach est le premier agent LLM. LangGraph orchestre un état typé avec budget
borné ; Analyste après partie et vérification des preuves sont ajoutés progressivement.
Une correction de réponse maximum, suivie d'un contrôle ou d'une abstention.

Après l'Analyste, privilégier le planificateur de progression. Réserver les
spécialistes patch/macro/micro à des besoins mesurés. L'évaluation reste hors ligne.

## Conséquences et validation

Ajouter un stockage structuré et des contrats d'état à tester. Conserver une
baseline simple pour comparer pertinence, latence et coût. Les chiffres exacts
viennent de lookups/calculs ; les conseils inférés sont signalés. Aucun nouveau
stockage ou agent n'est livré par ce document.

Validation attendue : ingestion rejouable, filtres patch/langue, provenance
jusqu'à la réponse, tests des transitions et budgets, contrôle des citations,
abstention hors corpus et évaluation avant/après chaque agent supplémentaire.

## Options examinées

- Tout stocker dans Qdrant : moins adapté à l'audit des données brutes et aux lookups exacts.
- Un LLM par étape : coûts et indéterminisme inutiles pour collecte et calculs.
- Superviseur libre dès le début : plus difficile à tester et borner qu'un workflow explicite.

Le détail des flux et rôles figure dans l'[architecture](../architecture.md).
