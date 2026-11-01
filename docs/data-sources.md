# Sources, provenance et limites

## Périmètre initial

Le premier corpus doit pouvoir fonctionner avec les sources officielles Riot.
Le package `src/nexusmind/` implémente ce parcours sans importer les intégrations
tierces. Celles-ci restent dans les dossiers historiques, hors package ; aucune
disponibilité de scraping n'est présumée. CommunityDragon est communautaire et
ne fait pas partie du périmètre Riot uniquement. Après le jalon `POC`, son
connecteur explicite, le guide Riot et l'import attribué étendent ce premier
périmètre : voir le [guide d'enrichissement](knowledge-sources.md) et
l'[ADR-0009](decisions/0009-knowledge-sources.md). L'ingestion Data Dragon par
défaut n'appelle toujours aucun fournisseur tiers.

| Source | Usage prévu | Limite à respecter |
| --- | --- | --- |
| Data Dragon | Champions, sorts, objets, runes et textes descriptifs | Référence statique versionnée, pas un manuel exhaustif de coaching |
| Notes de patch officielles | Changements et contexte de version | Extension ultérieure via accès autorisé et extracteur dédié, pas un flux déjà implémenté |
| API Account / Match-v5 | Identifier le joueur, analyser une partie terminée et sa timeline | Parcours implémenté dans le package maintenu ; clé valide requise, collecte bornée et données minimisées |
| Spectator / Live Client | Expérimentations ciblées, ultérieures | Ne pas confondre liste des participants et télémétrie complète ; Live Client est local au joueur |

La documentation Riot décrit le contenu et le versionnement de
[Data Dragon](https://developer.riotgames.com/docs/lol#data-dragon).
Elle distingue les [routages plateforme et régional](https://developer.riotgames.com/docs/lol#routing-values).
Vérifier chaque endpoint dans la [référence API officielle](https://developer.riotgames.com/apis)
au moment de l'implémentation ; ne pas recopier les URL historiques du parser.
Pour EUW, distinguer par exemple la plateforme `euw1` de la région `europe`.

## Contrat documentaire cible

Chaque document et ses chunks conservent :

| Champ logique | Signification |
| --- | --- |
| `document_id`, `chunk_id` | Identifiants stables et dédupliquables |
| `source_name`, `source_url` | Provenance réelle ; endpoint expurgé pour les données joueur |
| `source_version`, `game_patch`, `locale` | Version du fournisseur, patch et langue, sans les confondre |
| `retrieved_at` | Date UTC avec fuseau |
| `entity_type`, `entity_id`, `section` | Champion/objet/sort et passage concerné |
| `text`, `content_hash` | Texte réellement encodé et contrôle de changement |
| `embedding_model`, `embedding_revision` | Compatibilité du vecteur avec la requête |
| `schema_version` | Version du format d'indexation |

Les nouveaux passages de référence ajoutent notamment `source_id`, `source_key`,
`source_revision`, `title`, `content_kind`, `license_name`, `license_url`,
`attribution` et `topics`. Leur patch peut être `unversioned`, sans être réécrit
en patch courant. Les anciens payloads restent lisibles.

Le payload courant contient `id`, `entity_type`, `entity_id`, `section`, `text`,
`patch`, `locale`, `source_name`, `source_url`, `retrieved_at`, `content_hash`,
`schema_version`, `embedding_model` et `embedding_revision`. L'identifiant `id`
est celui du passage. Les noms plus détaillés du tableau restent la cible à
adapter avec migration si nécessaire. Distinguer document
brut, objet métier et passage indexable. Nettoyer le HTML et les placeholders
sans interpréter une formule non résolue comme une valeur réelle. Découper par
champion, sort ou section avant d'ajuster les tailles par mesure.

Choisir explicitement la version Data Dragon disponible, l'enregistrer et la
réutiliser pour le lot entier. Ne pas annoncer un patch courant uniquement à
partir de la date. Une ancienne version ne doit pas être mélangée silencieusement
avec la nouvelle ; tout fallback de langue ou version est visible.

## Accès et erreurs

Ajouter timeout, retries bornés avec backoff pour les erreurs transitoires et
cache versionné. Sur `429`, respecter `Retry-After`, conformément au
[portail Riot](https://developer.riotgames.com/docs/portal#response-codes).
Traiter séparément authentification refusée, ressource absente et panne serveur.
Ne pas boucler sur une clé invalide. Les quotas doivent être coordonnés entre
travailleurs ; ajouter des agents n'augmente pas le quota autorisé.

Avant diffusion à des joueurs, vérifier l'enregistrement du produit et les
conditions applicables dans les [règles générales Riot](https://developer.riotgames.com/policies/general)
et les [règles LoL](https://developer.riotgames.com/docs/lol#developer-api-policy).
Ces liens sont des références externes consultées le 31 octobre 2026, à revalider
lors d'une évolution des sources ou d'une publication.

## Ce que le coach peut affirmer

Les textes descriptifs et statistiques permettent des réponses factuelles.
L'analyse des matchs peut apporter des mesures, mais une corrélation dans une
timeline ne prouve pas la cause d'une défaite. Un conseil macro/micro reste une
hypothèse tant qu'une source ou une observation ne le justifie pas.

Format attendu : réponse directe, fait sourcé et patch, raisonnement explicite,
limite éventuelle, exercice adapté au joueur. Si la question dépasse le corpus,
le dire et demander le contexte utile. Ne pas inventer un winrate global, un
timer actuel, la position d'un ennemi ou une interaction absente des sources.
Les sujets non couverts restent dans le jeu d'évaluation comme cas d'abstention.

Minimiser les identifiants joueur, pseudonymiser les fixtures, exclure les clés
et données personnelles des logs et du dépôt. Définir durée de conservation et
suppression avant de stocker durablement un historique de joueurs.

Le [guide après partie](postgame.md) définit le parcours livré : quatre appels
maximum, mesures calculées, données en mémoire, endpoints expurgés et sauvegarde
locale uniquement sur demande. Les tests synthétiques ne prouvent pas qu'une
clé personnelle donnée est valide ; voir la [validation](validation/postgame-2026-11-01.md).
