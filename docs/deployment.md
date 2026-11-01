# CI/CD et déploiement propre

## Statut

Le workflow [CI](../.github/workflows/ci.yml) existe désormais pour le package
maintenu. Une API locale et un chat existent via l'extra `web` ; aucun
Dockerfile, Compose ou déploiement cloud n'est fourni.
Les sections de livraison ci-dessous restent la cible ; la CI ne déploie rien.

## Piste cloud avec un budget de zéro euro

Recommandation au 1er novembre 2026 : conserver l'inférence du Coach sur l'API
Gemini gratuite, puis conteneuriser l'application et Qdrant. Commencer localement
avec Docker Compose ; pour apprendre Kubernetes, tester K3s en local puis sur
une VM Oracle Always Free éligible. Aucun compte, cluster ou service cloud n'a
été créé par ce chantier. Le [guide Coach](coach.md) détaille la condition de
projet Gemini sans facturation.

La documentation Oracle indique actuellement un total Ampere A1 équivalent à
**2 OCPU et 12 Go de RAM**, avec 200 Go de volumes Always Free partagés avec les
disques de démarrage. Les ressources doivent respecter l'éligibilité et la
région d'origine. La capacité peut être indisponible ; les instances inactives
peuvent être récupérées par Oracle. Ce n'est pas une garantie d'hébergement
permanent. Source : [Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm).

K3s prend en charge ARM64 et demande au minimum 2 cœurs et 2 Go pour le serveur,
en plus des ressources de l'application. Une VM unique constitue une piste à
mesurer pour cette petite application ; ce n'est pas de la haute disponibilité.
Source : [prérequis K3s](https://docs.k3s.io/installation/requirements).

Avant ce déploiement : API/interface, évaluation réelle du Coach, images ARM64
testées (notamment PyTorch), mémoire mesurée, Qdrant serveur validé, volumes
persistants et restauration, authentification et limites de requêtes. Le Scout
sera un traitement ponctuel/CronJob hors des requêtes joueur. Ne pas ouvrir
publiquement Qdrant ; exposer l'application via un ingress HTTPS. Vérifier les
coûts de chaque ressource réseau/stockage, sans supposer qu'un cluster managé
ou un crédit d'essai soit gratuit durablement. Un quota LLM épuisé doit rendre
le Coach indisponible jusqu'à son renouvellement, sans bascule payante.

## CI du package maintenu

Job réel : `python-checks`, workflow `CI`, sur les PR vers `dev`/`main` et les
pushes de ces branches. Il installe Python 3.12 avec uv 0.12.18, synchronise le
lock, contrôle Ruff, exécute les tests hors ligne, construit le package et vérifie
la CLI. PyTorch utilise l'index CPU sur Linux ; aucun téléchargement de modèle
ni appel Riot n'est nécessaire aux tests. Qdrant y fonctionne en mémoire.
Configurer `python-checks` comme contrôle requis seulement après sa première
exécution réussie ; la création du workflow ne modifie pas les rulesets GitHub.

## Évolutions de CI

Ajouter une intégration Qdrant serveur avec version d'image fixée et stockage
éphémère lorsque ses tests existent. Les contrôles mémoire actuels ne prouvent
pas la compatibilité opérationnelle d'un serveur distant.

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

Le [chat et l'API locale](web.md) sont disponibles, avec lifespan et routes
de santé. L'authentification publique et les quotas distribués restent à définir.

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
