# Instructions pour les agents de développement

NexusMind est un projet personnel d'apprentissage du RAG, de l'orchestration
multi-agents et du déploiement, appliqué à un coach League of Legends.
Ces instructions concernent les agents qui modifient le dépôt. Les agents
Scout, RAG et Coach sont des composants du produit.

## Lire avant d'agir

- [Index documentaire](docs/README.md) : parcours de lecture et statut des documents.
- [Audit de l'existant](docs/audit.md) : faits observés, défauts et limites de vérification.
- [Architecture](docs/architecture.md) : responsabilités, contrats et architecture cible.
- [Sources et qualité des données](docs/data-sources.md) : périmètre Riot, provenance et limites du coaching.
- [Enrichissement après le POC](docs/knowledge-sources.md) : connecteurs approuvés,
  import attribué, révisions, routage et sources désactivées.
- [Contrats des connecteurs](docs/source-connectors.md) et
  [validation des sources](docs/validation/knowledge-2026-11-01.md) : API et preuves.
- [Développement local](docs/development.md) : environnement, commandes et conventions Python.
- [Ingestion Scout](docs/ingestion.md) : installation, collecte Riot et recherche de contrôle.
- [Validation Scout](docs/validation/scout-2026-10-31.md) : résultats réels et limites de vérification.
- [Retrieval et évaluation](docs/retrieval.md) : commandes, contrats et protocole.
- [Validation retrieval](docs/validation/retrieval-2026-10-31.md) : mesures avant/après et limites.
- [Coach](docs/coach.md) : Gemini gratuit, commandes, bornes et limites de validation.
- [Validation Coach](docs/validation/coach-2026-11-01.md) : premier lot réel partiel, latence et limites.
- [Latence Coach](docs/validation/coach-latency-2026-11-01.md) : comparaison des profils et mesures réelles.
- [Chat et API locale](docs/web.md) : runtime persistant, commandes et portée.
- [Analyse après partie](docs/postgame.md) et [validation](docs/validation/postgame-2026-11-01.md) : mesures Match-v5, confidentialité et limites.
- [Git et GitHub](docs/git-workflow.md) : branches, commits atomiques, PR et versions.
- [TDD et évaluation RAG](docs/testing.md) : Red/Green/Refactor et critères de qualité.
- [Déploiement](docs/deployment.md) : CI/CD cible, secrets, exploitation et rollback.
- [Feuille de route](docs/roadmap.md) : ordre des chantiers et critères d'acceptation.
- [Décisions d'architecture](docs/decisions/README.md) et
  [ADR-0001](docs/decisions/0001-riot-first.md) et
  [ADR-0002](docs/decisions/0002-rag-orchestration.md) et
  [ADR-0003](docs/decisions/0003-python-package-layout.md) et
  [ADR-0004](docs/decisions/0004-retrieval-baseline.md) et
  [ADR-0005](docs/decisions/0005-free-tier-coach.md) et
  [ADR-0006](docs/decisions/0006-low-latency-coach.md) et
  [ADR-0007](docs/decisions/0007-local-coach-interface.md) et
  [ADR-0008](docs/decisions/0008-postgame-analysis.md) et
  [ADR-0009](docs/decisions/0009-knowledge-sources.md) : décisions structurantes.
- [Modèle de PR](.github/pull_request_template.md),
  [demande de fonctionnalité](.github/ISSUE_TEMPLATE/feature.md) et
  [signalement de bug](.github/ISSUE_TEMPLATE/bug.md) : supports de contribution.

Lire systématiquement l'audit, le workflow Git et les tests ; lire les autres
documents selon les fichiers touchés. L'existant et la cible sont distincts :
ne jamais annoncer comme opérationnel un composant seulement documenté.

## Règles de travail

1. Inspecter la branche, le statut et le diff avant toute modification. Préserver
   les changements locaux de l'utilisateur. Ne pas les committer avec son travail.
2. Définir un objectif vérifiable et une tranche courte. Pour un comportement
   nouveau ou corrigé, écrire un test qui échoue pour la bonne raison, implémenter
   le minimum puis refactorer. Pour la documentation seule, vérifier liens,
   commandes et cohérence ; pas de tests applicatifs artificiels.
3. Suivre `main` / `dev` / `feat/*` / `fix/*` et les exceptions décrites dans le
   workflow. `dev` est initialisée depuis l'historique committé de `scout`, qui
   contient celui de `develop`. Ne pas renommer ou supprimer les branches historiques
   à l'occasion d'une autre tâche.
4. Produire des commits Conventional Commits, chacun cohérent, vérifiable et
   réversible. Inclure ensemble le test et son implémentation. Avant un commit,
   sélectionner les chemins ou hunks, puis lire le diff indexé. Aucun `git add .`
   aveugle. Ne pas créer de commit ou pousser pour une simple demande d'édition.
5. Le POC reste Riot uniquement. L'extension demandée après ce jalon autorise les
   connecteurs décrits dans `docs/knowledge-sources.md` et l'ADR-0009, sans réactiver
   les anciens parsers. Ne pas contourner un blocage, changer d'identité après un
   refus ou acheter un abonnement. Vérifier l'accès et la provenance avant toute
   source supplémentaire ; le Wiki et les sites statistiques restent désactivés.
6. Une donnée absente reste absente : ne pas fabriquer un winrate, une position,
   un rayon de vision ou un vecteur de remplacement. Une panne de retrieval
   doit être distinguée d'une absence de résultats.
7. Conserver source, version, langue et date de collecte jusqu'à la réponse.
   Séparer fait sourcé, mesure calculée et hypothèse de coaching. Ne pas traiter
   un score de similarité comme une probabilité de vérité.
8. Injecter les dépendances externes pour tester sans réseau, clé, Qdrant réel
   ni téléchargement de modèle. Ne jamais lancer `main.py` comme test unitaire :
   il collecte et écrit dans Qdrant.
9. Ne pas exposer les secrets, lire ou afficher `.env` pour un audit courant,
   versionner des données personnelles, logs ou volumes Qdrant. Ne pas supprimer
   un volume ou recréer une collection sans stratégie de migration explicite.
10. Toute évolution de contrat, source, configuration ou commande s'accompagne
    de sa documentation. Toute décision structurante nécessite un ADR.
11. Terminer avec les changements, les vérifications réellement exécutées et
    leurs limites. Un contrôle non exécuté reste signalé comme tel.

## Outils et portabilité

Dans cet environnement, lire et respecter `C:\Users\user\.codex\RTK.md` s'il
est accessible ; préfixer les commandes shell par `rtk` conformément à cette
instruction locale. Ce chemin personnel n'est pas une dépendance du projet.
Si RTK n'est pas installé ailleurs, utiliser les commandes sous-jacentes et
signaler cette différence. Vérifier le répertoire effectif : utiliser `git -C`
et des chemins explicites si le lanceur ignore le répertoire demandé.

La documentation est en français, les identifiants Python et les sujets de
commits en anglais. Respecter la casse exacte des modules, notamment pour Linux.

## Code maintenu

Ajouter le code dans `src/nexusmind/` et les tests dans `tests/`. Garder le domaine
indépendant des adaptateurs et injecter leurs ports dans l'application. La CLI
supportée est `uv run nexusmind`, pas le `main.py` historique. Les anciens dossiers
racine sont conservés pour migration, sans ajout de nouveaux comportements.
Exécuter `uv run --extra web pytest -q`, `uv run --extra web ruff check src tests` et
`uv run --extra web ruff format --check src tests` (avec le préfixe RTK local). La suite est
hors ligne et utilise Qdrant en mémoire ; ne pas la confondre avec une validation
sur serveur distant ou une évaluation pédagogique du RAG.
