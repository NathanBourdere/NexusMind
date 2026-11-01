# Documentation NexusMind

Point d'entrée pour les humains et les agents : [AGENTS.md](../AGENTS.md).
Les documents décrivent un état inspecté le **31 octobre 2026**, puis les règles
à suivre et la cible. Ils ne prouvent ni le bon fonctionnement de la démo ni
l'activation de protections sur GitHub.

| Document | Quand le lire | Nature |
| --- | --- | --- |
| [Audit](audit.md) | Avant de corriger ou planifier | État observé |
| [Architecture](architecture.md) | Avant de modifier agents ou contrats | Existant et cible |
| [Ingestion Scout](ingestion.md) | Pour installer, collecter et vérifier l'index | Parcours maintenu |
| [Validation Scout](validation/scout-2026-10-31.md) | Pour consulter les résultats réels et leurs limites | Preuves datées |
| [Retrieval](retrieval.md) | Pour récupérer des preuves ou évaluer la recherche | Parcours maintenu |
| [Validation retrieval](validation/retrieval-2026-10-31.md) | Pour lire la baseline et ses limites | Mesures datées |
| [Coach](coach.md) | Pour configurer Gemini gratuit et expliquer les preuves | Implémenté, première réponse réelle vérifiée |
| [Validation Coach](validation/coach-2026-11-01.md) | Pour lire les vérifications réellement effectuées | Lot réel partiel et limites |
| [Latence Coach](validation/coach-latency-2026-11-01.md) | Pour comparer Flash et Flash-Lite | Mesures réelles sur un petit échantillon |
| [Chat et API](web.md) | Pour utiliser le Coach sans recharger l'encodeur | Interface locale |
| [Sources](data-sources.md) | Avant de collecter ou indexer | Politique et contrats cibles |
| [Développement](development.md) | Pour préparer l'environnement | Commandes et limites actuelles |
| [Git/GitHub](git-workflow.md) | Pour toute contribution | Convention et configuration à appliquer |
| [Tests](testing.md) | Pour tout changement de comportement | Méthode et outillage à installer |
| [Déploiement](deployment.md) | Avant une CI, release ou mise en ligne | Procédure cible |
| [Roadmap](roadmap.md) | Pour choisir la prochaine tranche | Travail restant |
| [ADR](decisions/README.md) | Pour changer une décision structurante | Historique des décisions |

Une PR qui modifie un comportement doit mettre à jour le document concerné.
L'audit est une photographie datée ; y ajouter une note datée ou une référence
de résolution lorsque ses constats sont corrigés, sans réécrire l'histoire.
