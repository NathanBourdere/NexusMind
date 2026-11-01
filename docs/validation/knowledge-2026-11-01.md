# Validation de l'enrichissement — 1er novembre 2026

Cette vérification porte sur les nouveaux connecteurs et leur intégration. Elle
ne remplace pas une évaluation pédagogique du futur corpus macro/micro.

## Collecte et stockage réels

- Identité `NexusMind/0.1`, endpoints publics, sans clé, abonnement ou crawler.
- Guide Riot français : six chapitres ; CommunityDragon `16.21` français : Ahri
  (`103`) et Ezreal (`81`), sans données de joueur.
- Résultat : **8 articles et 41 passages** avec le modèle multilingue fixé à la
  révision déjà utilisée par le POC.
- Stockage de contrôle isolé dans `.runtime/knowledge-preview`, distinct du
  Qdrant du chat. Rejeu réel : **41 points avant et après**, rapport terminé.
- Révisions, attribution, conditions et patch réel conservés dans les payloads.
  Aucune collection existante n'a été recréée ni supprimée.

## Retrieval et génération

Cinq questions de contrôle, choisies pour ce chantier :

| Question | Mode | Résultat attendu et observé |
| --- | --- | --- |
| Pourquoi attaquer une tourelle avec des sbires ? | auto | Preuve du guide Riot, patch explicitement non versionné |
| À quoi sert le rôle support ? | auto | Preuves du guide Riot |
| Quel est le fonctionnement du Q de Ahri ? | reference | Texte du Q CommunityDragon, version `16.21`, placeholders conservés |
| Comment freeze une vague avec Ahri ? | auto | Hors périmètre, aucun LLM |
| Quel est le winrate de Ahri ? | auto | Hors périmètre, aucun LLM |

Deux réponses Gemini relues contre leurs passages après correction du filtrage
par compétence : le cas tourelle et le Q d'Ahri. Les citations viennent bien des
passages fournis ; les versions restent distinctes de `16.21.1`. Les durées de
génération mesurées sont respectivement **1 529,699 ms** et **1 922,875 ms**, hors
chargement du modèle et retrieval. Deux exemples ne définissent pas une médiane
ou un p95 représentatif.

Le premier essai avait répondu au cas tourelle mais s'était abstenu sur Ahri.
Un test de régression a reproduit l'absence de filtre par compétence ; le
retrieval référence sélectionne désormais le Q avant classement. Deux appels
initiaux puis deux appels de contrôle : **quatre tentatives Gemini au total**,
sans retry automatique. Le lot de cinq questions n'est pas une suite indépendante.

Les artefacts bruts de collecte et les réponses restent dans `.runtime/`, hors
Git. Le corpus du guide peut être ancien : le statut non versionné n'est pas
une garantie d'actualité. Le modèle n'a reçu aucune donnée de partie.

## Contrôles et limites

La suite hors ligne couvre transport, refus, extraction, provenance, rejeu,
édition immuable, interruption après un premier batch, version active, patch et
langue, filtres explicites, sélection du sort, abstention, contexte Gemini et
conservation des citations via HTTP. Elle utilise Qdrant en mémoire et des
doubles, sans réseau ni modèle téléchargé.

Vérification locale finale : **137 tests passés**, Ruff check réussi et
**48 fichiers Python** conformes au formatage. Le premier commit de connecteurs
a aussi été exporté et testé indépendamment du second : **118 tests passés**.

La syntaxe JavaScript est contrôlée avec `node --check`. Le rendu visuel des
nouvelles cartes de sources reste à vérifier dans un navigateur. Ni serveur
Qdrant distant, ni corpus Wiki, LoLalytics ou Leaguepedia, ni pédagogie avancée
n'ont été validés. La suite de 37 questions du POC n'a pas été rejouée en live
avec ce nouveau prompt ; ses anciens scores ne sont pas transposés ici.
