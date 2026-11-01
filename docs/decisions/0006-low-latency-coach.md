# 0006 — Profil Coach rapide avec Flash-Lite

Date : 2026-11-01
Statut : accepté, remplace le modèle par défaut de l'ADR-0005

## Contexte

Le premier Coach `gemini-3.8-flash` avec raisonnement `LOW` a mis environ
69 secondes pour expliquer un sort à partir d'un passage court. Le propriétaire
demande une réduction de latence en conservant le budget de zéro euro.
La durée mesurée concernait la génération et la validation, hors chargement
du modèle d'embedding et retrieval.

## Décision

Utiliser par défaut `gemini-3.5-flash-lite`, avec le raisonnement `MINIMAL`
supporté par ce modèle. Conserver `gemini-3.8-flash` avec `LOW` comme choix
explicite via `--coach-model`, dans `coach` et `evaluate-coach`. Accepter
uniquement ces deux profils dont l'offre gratuite a été vérifiée à cette date.
Un projet sans facturation reste nécessaire ; le code ne le vérifie pas.

Conserver les mêmes prompt, contexte, schéma, limites de sortie et validation
des références : ce changement cible le fournisseur de génération. Aucun
cache de réponse ne masque les appels de comparaison, aucun retry ou fallback
automatique n'est introduit. L'encodeur et la collection Qdrant restent compatibles.

## Conséquences

Cinq mesures Flash-Lite sont entre 1,27 et 2,10 secondes. L'échantillon
est réduit ; les conditions du service gratuit et la qualité peuvent varier.
La comparaison et la relecture des réponses doivent être consignées, sans
présenter ce résultat comme une garantie de p95 ou de qualité générale.
Voir les [mesures détaillées](../validation/coach-latency-2026-11-01.md).

Le démarrage à froid de la CLI charge toujours l'encodeur. Une future API
persistante devra charger ses dépendances une fois au démarrage pour éviter
ce coût à chaque question. Aucun serveur HTTP n'est ajouté dans cette tranche.

Références : [tarifs Gemini](https://ai.google.dev/gemini-api/docs/pricing),
[niveaux de raisonnement](https://ai.google.dev/gemini-api/docs/thinking),
[guide Coach](../coach.md), [ADR-0005](0005-free-tier-coach.md).
