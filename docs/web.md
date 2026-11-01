# Chat local et API persistante

Le sélecteur « Sources » propose le mode automatique, les fiches Riot ou les
guides et données communautaires. Le champ JSON `corpus` vaut `auto`, `static`
ou `reference` (défaut `auto`). Les cartes de sources affichent fournisseur,
version réelle, langue, collecte, révision, attribution et conditions déclarées.
Voir le [guide d'enrichissement](knowledge-sources.md). Redémarrer le serveur
après une ingestion pour recharger son catalogue.

Le chat utilise FastAPI et une page HTML/JavaScript servie par la même application.
Le lifespan construit une fois l'encodeur, le client Qdrant, le catalogue en
mémoire et la session HTTP Gemini. Une question réutilise ces dépendances ;
elle ne réingère pas les données et ne recharge pas les poids.

## Lancement

Depuis la racine du checkout, avec le corpus existant et le `.env` local :

```powershell
rtk proxy uv sync --frozen --extra web
rtk proxy uv run --frozen --extra web --env-file .env nexusmind serve --patch 16.21.1 --offline-model --free-tier-confirmed
```

Ouvrir `http://127.0.0.1:8000`. `--port` change le port, `--data-dir` sélectionne
le corpus, `--coach-model` choisit un des deux profils Gemini autorisés et
`--max-calls` fixe le budget de génération du processus (30 par défaut, maximum
100). Les tentatives échouées consomment ce budget. Les abstentions avant LLM
n'en consomment pas. Le redémarrage remet ce compteur à zéro ; ce n'est pas
un quota journalier partagé ni une vérification de facturation.

Dans un worktree, fournir les chemins absolus du `.env` et du `.runtime` du
checkout principal, avec `/` sous Windows. L'installation de l'extra ne
déplace pas les données. Le démarrage peut prendre du temps : le serveur
accepte les requêtes après le chargement initial, puis réutilise le modèle.
Arrêter le serveur avant une ingestion locale pour libérer le verrou Qdrant.

## Parcours utilisateur et endpoints

La page permet de poser une question et de choisir son niveau. Elle affiche
faits sourcés, hypothèses, exercice, sources Riot, patch et limites. Les
clarifications montrent les identifiants proposés lorsque les noms sont ambigus.
L'historique affiché vit uniquement dans la page, sans stockage navigateur
persistant. Cette version traite chaque question indépendamment.

- `GET /` et `/assets/*` : interface locale, sans CDN.
- `GET /health/live` : processus actif, sans appel externe.
- `GET /health/ready` : dépendances chargées par le lifespan, sans appel Gemini.
- `GET /api/config` : patch et langue proposés dans l'interface.
- `POST /api/chat` : requête de retrieval plus `level`, avec cinq passages au plus.
- `POST /api/postgame` : analyse déterministe d'une partie, sans LLM. Le
  formulaire nécessite la clé Riot du serveur ; voir le [guide](postgame.md).

Une génération à la fois protège les ressources partagées ; une requête
concurrente reçoit HTTP 429. Les erreurs techniques sont explicites : quota
429, fournisseur indisponible 503, génération invalide 502. Un manque de preuves
reste une réponse fonctionnelle avec son statut, pas une panne.

## Portée et vérification

Le serveur écoute **uniquement sur 127.0.0.1**, sans authentification publique.
Les hôtes attendus et l'origine des requêtes sont contrôlés, les réponses sont
non mises en cache et les textes LLM sont affichés avec `textContent`. Les clés
restent côté serveur ; aucune API de collecte n'est exposée. Les logs d'accès
sont désactivés. Ce prototype local ne doit pas être exposé tel quel sur Internet.
Le cloud nécessitera authentification, quotas partagés, HTTPS, sauvegardes et
validation Qdrant serveur, comme décrit dans le [déploiement](deployment.md).

Les tests injectent le runtime, vérifient sa création unique, sa fermeture,
les requêtes invalides, les origines externes et le budget de génération. Ils
ne téléchargent aucun modèle et n'appellent pas Gemini. La CI installe l'extra
`web`. Voir l'[ADR-0007](decisions/0007-local-coach-interface.md).

## Vérification locale du 1er novembre 2026

Le serveur a démarré sur `127.0.0.1:8765` avec le corpus réel et l'encodeur
en cache. La page, le JavaScript, le CSS et la readiness ont répondu HTTP 200.
Deux requêtes successives ont reçu une réponse sourcée sans rechargement :
environ 11,8 s puis 4,6 s, cette fois avec retrieval et coût du premier encodage.
Les logs montrent un seul chargement des poids au démarrage. La syntaxe du
JavaScript a été vérifiée par `node --check`.

La tentative d'inspection visuelle a été bloquée par l'indisponibilité de
l'hôte de navigateur de l'outil ; le rendu et les interactions dans un vrai
navigateur restent à vérifier manuellement. Les tests HTTP ne les remplacent pas.
