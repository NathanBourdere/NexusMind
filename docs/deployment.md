# CI/CD et déploiement propre

## Statut

Aucun workflow GitHub Actions, Dockerfile, Compose ou déploiement opérationnel
n'a été observé dans les fichiers suivis. Cette page définit la cible ; elle ne
crée aucune infrastructure. Le premier livrable reste une exécution locale reproductible.

## CI après les fondations de test

Sur les PR ciblant `dev`/`main` et leurs pushes : checkout, Python 3.12, version
uv fixée, `uv sync --frozen` avec groupe de développement, lint/format et tests
unitaires hors ligne. Exécuter sous Linux pour la casse des imports. Ajouter
une intégration Qdrant avec version d'image fixée et stockage éphémère lorsque
ses tests existent.

Permissions du workflow limitées à la lecture pour les contrôles. Éviter le code
de PR non fiable avec secrets, notamment via `pull_request_target`. Aucun secret
Riot ou LLM pour les tests unitaires. Vérifier les liens documentaires relatifs ;
ne pas confondre panne externe et lien interne cassé.

Reporter les **noms réels** des jobs stables dans les protections GitHub. Aucun
badge vert ou annonce de CI avant son exécution.

## Artefact et environnements

1. Construire depuis un commit validé, avec dépendances verrouillées et image
   de base fixée. Tester installation et imports dans l'image finale.
2. Précharger le modèle/révision ou prévoir son cache contrôlé pour éviter un
   téléchargement surprise lors d'une requête.
3. Séparer développement, staging et production : configuration, secrets,
   collections et volumes distincts ; fixtures anonymisées.
4. Conteneur applicatif sans privilèges ; Qdrant sur réseau privé, volume
   persistant et accès authentifié selon l'environnement.
5. Quand le service HTTP existera, liveness sans dépendance externe et readiness
   vérifiant modèle, configuration et schéma Qdrant sans écriture.

Le frontend et l'API de service restent à définir. Ne pas inventer de routes
ou commandes de production dans le README.

## Secrets et données

Secrets injectés par environnement ou gestionnaire dédié, jamais dans image,
code, historique Git ou prompt journalisé. Fournir un exemple sans valeurs réelles
avec l'implémentation. En cas de fuite, révoquer/renouveler : supprimer le fichier
ne révoque pas la clé.

Exclure volumes Qdrant, cache de modèles et logs du dépôt et du contexte de build.
Sauvegarder avec versions du schéma et du modèle, puis tester la restauration
isolée avant d'annoncer une sauvegarde fiable.

## Release et retour arrière

Avant release : tests passés, évaluation sans régression convenue, configuration
documentée, secrets présents, version du corpus connue, smoke test en staging
et restauration testée si migration. Vérifier les [conditions des sources](data-sources.md)
avant ouverture à des joueurs.

Journaliser identifiant de requête, latence par étape, version du corpus,
résultat/erreur et consommation ; expurger secrets et données personnelles.
Mesurer abstentions, erreurs sources/Qdrant/LLM et durée d'ingestion. Fermer
proprement clients et tâches à l'arrêt.

Déployer l'artefact identifié par commit/tag. Conserver l'artefact précédent et
sa configuration compatible. Une évolution d'embedding/payload se fait dans une
nouvelle collection validée avant bascule ; garder l'ancienne pour rollback.
Aucune recréation destructive automatique.

En cas d'incident : arrêter l'ingestion fautive, revenir à l'artefact et au corpus
compatibles précédents, vérifier une question témoin et ouvrir un correctif avec
test de régression. Une migration irréversible exige une restauration spécifique ;
redéployer l'ancien code ne suffit pas.
