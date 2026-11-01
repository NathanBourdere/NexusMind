# 0004 — Retrieval explicite et évaluation sur corpus versionné

Date : 2026-11-01 (mesure initiale le 31 octobre)
Statut : accepté dans le chantier retrieval demandé par le propriétaire

## Contexte

La recherche existante ne filtrait que patch et langue. Elle pouvait renvoyer
des passages d'autres champions et n'exprimait ni intention hors corpus ni
ambiguïté entre variantes d'un même objet. Le Coach doit recevoir des preuves
structurées et leurs limites avant tout ajout de génération.

## Décision

Conserver `search` comme outil vectoriel brut et ajouter un cas d'usage
`Retriever`, injecté via le port `SearchIndex`, exposé par `retrieve`.
Résoudre les noms depuis les passages localisés du catalogue, appliquer type,
IDs, familles de sections, patch et langue dans Qdrant. Les IDs multiples
utilisent `MatchAny` ; les filtres se combinent par intersection. Ne pas choisir
silencieusement entre variantes ayant le même nom. Retourner les candidats
ou demander des filtres explicites ; distinguer absence, ambiguïté, intention
hors périmètre et panne technique.

L'encodeur et le format d'index ne changent pas. Aucune migration destructive.
Le routage de périmètre est lexical et conservateur, sans promesse universelle.
Le statut `ok` ne prouve pas le soutien d'une réponse, et le score n'est pas
une probabilité. Ne pas fixer un seuil cosinus comme garantie de vérité.

Publier une suite versionnée avec annotations et une évaluation avant/après sur
le même snapshot. Distinguer les groupes development/validation et les demandes
avec IDs explicites. Conserver tous les résultats et empreintes ; échouer si
un gold manque ou si le backend est indisponible.

## Conséquences

La mesure combine lookup de noms, filtrage et ranking vectoriel ; elle ne prouve
pas une amélioration du modèle sémantique seul. Le jeu est petit, rédigé et
audité pendant ce chantier : son groupe validation n'est pas un benchmark
indépendant ou aveugle. Les annotations ambiguës ont été corrigées pendant
l'audit du corpus avant publication. Aucun seuil de qualité général n'est fixé
comme blocage de release sur la seule base de cet échantillon.

Le futur Coach vérifiera que les passages soutiennent les affirmations et citera
leurs IDs/sources. La normalisation ultérieure devrait porter explicitement noms,
emplacements Q/W/E/R et modes de jeu plutôt que reconstruire ces données depuis
le texte v1. Une suite indépendante et plus de paraphrases sont nécessaires
avant d'étendre les garanties de qualité.
