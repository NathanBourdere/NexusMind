# ADR-0009 — Enrichissement explicite après le POC

- Date : 1er novembre 2026
- Statut : accepté pour les connecteurs livrés ; sources bloquées différées
- Contexte : demande du propriétaire d'élargir les sources après validation du POC

## Problème

Data Dragon suffit aux descriptions, pas à un coach macro/micro. Les anciens
parsers ne constituent pas une base opérationnelle : squelette CommunityDragon,
URL Wiki historiques, statistiques fictives ou erreurs silencieuses. L'ADR-0001
avait volontairement limité le premier incrément à Riot ; le propriétaire demande
maintenant une extension gratuite et traçable.

## Décision

Conserver l'ingestion Data Dragon par défaut. Ajouter un contrat `SourceArticle`,
un connecteur ciblé CommunityDragon RAW versionné, un extracteur du guide Riot
français et un import local attribué. La collecte et l'indexation sont deux
commandes distinctes, sans LLM. Le Scout archive et indexe ces articles sans
dépendre des dossiers historiques.

Ne pas activer le Wiki ou un site statistique sur la seule présence d'un ancien
parser. Aucun contournement de refus, rotation d'identités, abonnement ou
présomption d'accès aux API privées. Les statuts vérifiés sont consignés dans le
[guide des sources](../knowledge-sources.md).

Les références sont des concepts avec révision, patch réel ou absence explicite,
langue, conditions et attribution. Ces métadonnées traversent retrieval, contexte
LLM et citations. Les champs additionnels restent compatibles avec le corpus POC ;
aucune collection n'est supprimée. Les anciennes éditions restent conservées,
mais le retrieval ne sélectionne que la dernière édition complètement cataloguée.

Le mode automatique garde la priorité du retrieval statique. Un mode référence
explicite sert aux guides et aux descriptions client. Le routage lexical demeure
limité ; ne pas annoncer une réponse experte sur la seule similarité d'un passage.
Ne pas associer silencieusement une référence non versionnée au patch courant.

## Conséquences et vérification

Le POC reste figé sous le tag `POC`, commit `625b4fb`, directement sur `dev` à la
demande du propriétaire, sans promotion implicite vers `main`. C'est une exception
nommée au cycle des releases SemVer, pas une release de production.

Les tests couvrent refus HTTP/robots, provenance, extraction hors marketing,
rejeu, révisions, échec partiel, routage, patch/langue et citations HTTP/LLM.
Le corpus initial de cette extension est petit et introductif ; il ne suffit pas
à couvrir la macro avancée. Une évaluation dédiée et des guides autorisés restent
nécessaires avant d'élargir les affirmations du Coach.
