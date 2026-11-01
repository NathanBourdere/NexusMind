# Analyse après partie Riot

L'Analyste collecte une partie terminée avec Account-v1 et Match-v5, calcule
des mesures en Python et propose des exercices présentés comme hypothèses.
**Aucun appel LLM** et aucune écriture Qdrant ne sont nécessaires. Les données
personnelles de partie ne sont pas envoyées à Gemini.

## Utilisation

Ajouter une clé Riot de développement valide au `.env` local sous
`RIOT_API_KEY`. Ne pas la partager ni la committer. Les clés de développement
expirent normalement après 24 heures ; l'authentification refusée est explicite,
sans tentative automatique de renouvellement. Source :
[portail Riot](https://developer.riotgames.com/docs/portal#development-api-keys).

```powershell
rtk proxy uv run --frozen --env-file .env nexusmind analyze-match "Nom#TAG" --region EUW
```

Par défaut, la dernière partie disponible est choisie. `--match-id EUW1_123`
permet de demander une partie précise, qui doit appartenir au joueur et à la
plateforme sélectionnée. `--output .runtime/analysis.json` sauvegarde le rapport
localement, sans écraser un fichier existant. Sans cette option, rien n'est
enregistré. Cette commande ne charge pas l'encodeur.

Le [chat](web.md) propose aussi un formulaire « Ta dernière partie » via
`POST /api/postgame`, avec `riot_id`, `region` et éventuellement `match_id`.
La clé reste côté serveur. Redémarrer le serveur après changement du `.env`.

## Collecte bornée et provenance

Au plus quatre requêtes officielles : Riot ID → PUUID, identifiant de partie,
détails, timeline. Avec un identifiant de partie fourni, la liste n'est pas
appelée. EUW/EUNE/TR/RU utilisent `europe`, NA/BR/LAN/LAS `americas`, KR/JP
`asia`, OCE/SEA `sea`. La valeur plateforme sert à contrôler les identifiants
de parties ; aucun endpoint Match-v5 n'utilise le host plateforme.
Référence : [routages Riot](https://developer.riotgames.com/docs/lol#routing-values).

Les résultats conservent la version complète `gameVersion` de la partie, les
endpoints expurgés et la date UTC de collecte. Cette version n'est pas remplacée
silencieusement par une version Data Dragon. L'API n'est pas localisée : la
langue de la source est `null`, bien que les explications soient en français.
Le PUUID est utilisé en mémoire pour sélectionner le participant puis omis du
rapport, comme les identifiants et pseudonymes des autres joueurs.

## Mesures et limites

- CS : `totalMinionsKilled + neutralMinionsKilled` ; CS/min : CS divisés par
  `gameDuration` en secondes, multipliés par 60.
- KDA : `(kills + assists) / deaths`, non défini si aucun décès.
- Participation aux éliminations : `(kills + assists) / somme des kills de
  l'équipe × 100`, non définie si le dénominateur est nul ou absent.
- Or gagné, score de vision et dégâts aux champions : valeurs Riot observées,
  distinctes des ratios calculés.
- Écarts d'or et de CS vers dix minutes : différence avec l'unique adversaire
  ayant le même `teamPosition` Riot, sur la frame la plus proche dans ±30 s.
  L'instant exact de la frame est conservé. Rôle, adversaire ou frame absent :
  résultat `null`, aucune attribution de rôle inventée.
- Morts : timestamps des événements `CHAMPION_KILL` concernant le joueur.
- Objectifs après une mort : événements ennemis `ELITE_MONSTER_KILL` dans les
  90 secondes suivantes. Un événement n'est compté qu'une fois. Cela ne mesure
  ni les objectifs manqués ni une causalité de défaite. Les bâtiments ne sont
  pas inclus dans ce compteur.

Le calcul de durée prend en charge les versions modernes (12 et suivantes),
pour lesquelles Match-v5 exprime `gameDuration` en secondes. Les anciennes
versions sont refusées au lieu d'être interprétées avec une mauvaise unité.
Les modes sans rôles de lane exploitables ne fournissent pas d'adversaire
automatiquement. Les valeurs absentes restent `null` ; zéro n'est retourné
que lorsqu'il correspond aux données observées ou à un calcul défini.

Une timeline HTTP 404 donne un rapport `partial` conservant les mesures du
match. Une panne réseau/serveur n'est pas assimilée à une timeline manquante.
Les statuts distinguent `ok`, `partial`, `no_matches`, `not_found`,
`authentication_failed`, `rate_limited` et `unavailable`. Pas de retry sur clé
refusée. Un HTTP 429 conserve `Retry-After` et bloque les appels du client
jusqu'à son échéance ; aucun sommeil long n'occupe un worker. Le cooldown est
local au processus, pas distribué.

## Conservation et validation

Les réponses brutes ne sont pas archivées par ce parcours. Le formulaire ne
stocke pas de Riot ID dans le navigateur ; l'analyse affichée vit dans la page.
Les rapports explicitement sauvegardés dans `.runtime/` contiennent encore un
identifiant de partie et une chronologie personnelle : ils sont à conserver
localement et à supprimer selon le besoin, jamais à publier dans Git.

Les fixtures sont entièrement synthétiques. Les tests couvrent calculs, champs
absents, division par zéro, rôles inconnus, provenance, routing, erreurs de clé,
cooldown et interface HTTP. Voir l'[ADR-0008](decisions/0008-postgame-analysis.md)
et la [validation](validation/postgame-2026-11-01.md). Aucun conseil n'est un
diagnostic certain de tes décisions ou de la cause d'une défaite.
