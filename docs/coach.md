# Coach sourcé avec un budget nul

## État au 1er novembre 2026

Le package maintenu expose `nexusmind coach` : recherche existante → génération
Gemini → validation des références → résultat JSON. Aucun LangGraph ni serveur
HTTP n'est nécessaire. Le fournisseur est injecté dans `application.Coach` et
peut être remplacé sans modifier le domaine. Voir l'[ADR-0005](decisions/0005-free-tier-coach.md).

Le parcours complet est testé hors ligne avec Qdrant en mémoire et transport
HTTP simulé. Un premier lot réel a obtenu une réponse sur le Q d'Ahri avec
Gemini 3.8 Flash et traité les 13 cas négatifs sans appel LLM. La génération
a pris environ 69 secondes. Le lot Flash-Lite ultérieur a exécuté les 37 cas
(24 réponses, 13 abstentions ou clarifications) avec relecture par l'agent ;
la revue humaine indépendante reste à effectuer. Voir la
[validation datée](validation/coach-2026-11-01.md).
Après optimisation, cinq appels Flash-Lite sont mesurés entre 1,27 et 2,10 s,
hors démarrage et retrieval. Le [rapport de latence](validation/coach-latency-2026-11-01.md)
décrit la comparaison et ses limites.

## Choix du modèle et gratuité

L'adaptateur utilise par défaut `gemini-3.5-flash-lite`, dont les entrées et sorties
texte sont proposées gratuitement dans l'offre Free à la date de vérification.
C'est un point de départ à évaluer, pas un classement de modèles. Les quotas
effectifs dépendent du compte et sont visibles dans AI Studio.
L'essai réel avec une nouvelle clé a montré que `gemini-2.5-flash` est refusé
aux nouveaux utilisateurs (HTTP 404), malgré sa présence dans le catalogue.
L'API recommande `gemini-3.8-flash`, utilisé pour le premier essai réel. Le
profil rapide Flash-Lite est ensuite devenu le défaut après mesure de latence ;
voir l'[ADR-0006](decisions/0006-low-latency-coach.md).
Sources : [tarifs officiels](https://ai.google.dev/gemini-api/docs/pricing),
[quotas](https://ai.google.dev/gemini-api/docs/rate-limits),
[contrat REST](https://ai.google.dev/api/generate-content).

Pour respecter un budget strict de zéro euro :

1. Créer une clé dans [Google AI Studio](https://aistudio.google.com/), pour un
   projet **sans facturation activée**. Ne pas activer de plan payant.
2. Vérifier que le modèle est disponible gratuitement pour ce projet et ce pays.
3. Injecter `GEMINI_API_KEY` dans l'environnement du processus, hors dépôt.
   `.env` n'est pas chargé automatiquement. Ne pas coller la clé dans le chat,
   un argument CLI ou un fichier suivi par Git.
4. Ajouter `--free-tier-confirmed` pour attester cette vérification. Ce drapeau
   ne change pas la facturation et ne la vérifie pas auprès de Google.

Le code ne crée aucun abonnement et ne sait pas reconnaître un projet facturé.
Une clé d'un projet payant peut entraîner des frais malgré ce drapeau : la
condition de gratuité est bien l'état du compte et de l'offre fournisseur.
Les conditions peuvent changer ; les revérifier avant une mise en ligne.
Les conditions d'utilisation des données dépendent notamment de la région et
du statut de facturation : consulter les
[conditions Gemini](https://ai.google.dev/gemini-api/terms). La version actuelle
envoie la question, le niveau, le patch et les textes Riot sélectionnés ; elle
n'envoie pas l'historique de parties ou les identifiants de joueur.

## Utilisation

Depuis ce checkout, avec le corpus ingéré et la clé injectée :

```powershell
rtk proxy uv run --frozen nexusmind coach "Explique le passif de Ahri" --patch 16.21.1 --free-tier-confirmed --offline-model
```

`--offline-model` concerne uniquement l'encodeur : Gemini nécessite Internet.
Pour un essai depuis ton terminal sans configurer de variable d'environnement,
ajouter `--prompt-api-key`. La saisie est masquée et la clé n'est pas enregistrée
par l'application. Cette option exige un terminal interactif ; elle n'envoie
pas la clé dans les arguments ni dans un fichier. Si `GEMINI_API_KEY` existe,
sa valeur est utilisée en priorité.

Si la clé est déjà dans un `.env` local, uv peut le charger explicitement, sans
ajouter de dépendance ni afficher le fichier :

```powershell
rtk proxy uv run --env-file .env --frozen nexusmind coach "Explique le passif de Ahri" --patch 16.21.1 --free-tier-confirmed --offline-model
```

Pour un `.env` situé dans un autre checkout, utiliser son chemin absolu avec
des `/` sous Windows, par exemple `--env-file C:/chemin/NexusMind/.env`.
Le fichier doit définir `GEMINI_API_KEY`. Il reste local et ignoré par Git ;
ne pas l'ajouter aux commits. Le même préfixe uv fonctionne avec `evaluate-coach`.
Les options de [retrieval](retrieval.md) restent disponibles : `--entity-type`,
`--entity-id` répété, `--section`, patch et langue explicites. Le Coach limite
`--limit` à 1–5. `--level` accepte `beginner` (défaut), `intermediate` ou
`advanced`. Le texte généré est en français dans cette première version.

Les options communes `--data-dir`, `--qdrant-url`, `--model` et `--revision`
concernent l'index et l'encodeur ; `--model` ne change pas le modèle Gemini.
`--coach-model gemini-3.5-flash-lite` sélectionne le profil rapide par défaut,
avec raisonnement `MINIMAL`. `--coach-model gemini-3.8-flash` conserve l'ancien
profil avec raisonnement `LOW`. Ces deux choix existent aussi pour
`evaluate-coach` ; aucun basculement automatique n'est effectué en cas d'erreur.
Le démarrage à froid de l'encodeur peut prendre du temps.

Le JSON contient :

- `claims` : affirmations courtes, type `sourced_fact` ou `coaching_hypothesis`,
  et `evidence_ids` pointant vers les passages utilisés ;
- `exercise` : proposition d'exercice d'observation ;
- `sources` : passages originaux avec URL Riot, patch, langue, date de collecte,
  modèle d'embedding et score ; le score n'est pas une probabilité de vérité ;
- `limitations`, candidats de clarification et identifiant du modèle appelé.

Statuts conservés du retrieval : `out_of_scope`, `needs_clarification`,
`no_results`, `unavailable`. Aucun appel LLM pour ces statuts.
Statuts de génération : `answered`, `insufficient_evidence`, `invalid_generation`
et `quota_exceeded`. Les erreurs techniques, sorties invalides et quotas ont un
code de sortie 1 ; les abstentions fonctionnelles ont un code 0.

## Limites et bornes

Un seul appel Gemini par commande, aucun retry ou modèle de secours. Timeout
connexion 5 s / lecture 90 s (pas une échéance totale garantie), cinq passages,
8 000 caractères de texte maximum, 2 048 tokens de sortie maximum, raisonnement
interne réglé sur `MINIMAL` (Flash-Lite) ou `LOW` (Flash). Un HTTP 429 arrête la
commande. Pas d'outil de recherche web,
de cache Gemini payant ou de réingestion déclenchée par une question.

Le domaine rejette un contexte mélangeant patches/langues, les références
inconnues et une réponse vide annoncée comme réussie. Les réponses tronquées,
bloquées ou non conformes au JSON sont rejetées. Les erreurs ne reproduisent
ni corps fournisseur, ni clé, ni URL de requête dans la sortie Coach.
En cas d'indisponibilité, `provider_status` conserve le statut HTTP éventuel et
`provider_error` distingue HTTP, timeout et transport, sans corps de réponse.

Ces contrôles prouvent l'appartenance des références, **pas le soutien
sémantique de chaque phrase**. Le prompt demande une abstention si la couverture
est insuffisante ; ce comportement doit encore être mesuré avec le vrai modèle.
Le filtrage hors corpus est lexical et incomplet. Data Dragon ne constitue pas
une base pédagogique macro exhaustive. Aucun chiffre absent n'est à compléter
de mémoire. Aucun juge LLM supplémentaire n'est exécuté.

## Validation avant publication

Les tests couvrent les abstentions sans appel, la provenance, les citations
inventées, le contexte invalide, les erreurs HTTP, le quota et le roundtrip CLI.
Ils ne contactent aucun fournisseur et ne nécessitent aucune clé réelle.

Avec une clé gratuite, vérifier au minimum des descriptions de passifs/sorts,
un objet à ID explicite, un nom ambigu, un patch absent, une question de winrate
et une question macro. Tester deux niveaux sur une même preuve et une tentative
d'instruction dans la question. Consigner question, corpus, modèle/date, statut,
citations, faits soutenus, erreurs et utilité pédagogique dans un rapport daté.
Ne pas publier de clé ou donnée personnelle. Examiner les nombres et les
exercices manuellement ; zéro référence inventée et abstention sur les cas hors
corpus sont les premiers critères. Une évaluation du Coach ne remplace pas la
[baseline retrieval](validation/retrieval-2026-10-31.md).

Le [déploiement](deployment.md) décrit la piste cloud gratuite et les éléments
encore nécessaires avant exposition publique.

## Exécution reproductible de la validation

`evaluate-coach` réutilise les 37 questions de retrieval. Les passages attendus
permettent de vérifier la disponibilité du corpus, mais ne constituent pas des
annotations sémantiques complètes pour les réponses. Ne pas transformer un
statut `answered` en score d'exactitude.

Préparer le plan sans clé et sans appel Gemini, depuis le checkout Coach :

```powershell
rtk proxy uv run --frozen nexusmind evaluate-coach --suite evaluation/retrieval-v1.json --output .runtime/coach-plan.json --offline-model
```

Pour un worktree, fournir `--data-dir` avec le chemin absolu du `.runtime`
contenant déjà le catalogue et Qdrant ; aucun besoin de relancer l'ingestion.
L'encodeur est chargé une seule fois et doit déjà être en cache en mode offline.

Après injection de `GEMINI_API_KEY` pour un projet sans facturation :

```powershell
rtk proxy uv run --frozen nexusmind evaluate-coach --suite evaluation/retrieval-v1.json --output .runtime/coach-live.json --offline-model --live --free-tier-confirmed --max-calls 3
```

La même commande accepte `--prompt-api-key` pour saisir la clé localement.

Le budget accepte 1 à 30 tentatives ; il compte les appels échoués aussi. Les
abstentions du retrieval ne consomment pas de budget. Les passages attendus
sont vérifiés avant tout appel Gemini, et toute panne de retrieval empêche la
génération du lot. Quota, réponse invalide et panne de génération arrêtent le
lot sans retry. Les cas non exécutés restent dans le rapport ; aucune reprise
automatique ne relance des appels. Un nouveau lancement est un nouveau budget.
`--call-interval` espace les générations de cinq secondes par défaut (0 à 60 s),
hors mesure de latence, pour limiter les rafales. Cela ne garantit pas un quota
compatible avec tous les comptes ; un HTTP 429 arrête toujours le lot.

Les états du rapport sont `planned`, `completed`, `partial` (budget atteint) ou
`stopped` (erreur, code de sortie 1). `partial` n'est pas une validation complète.
Le rapport conserve le contexte, les réponses, les références, les empreintes
du corpus et de la suite, le modèle, les durées et les statuts. Le nombre
d'appels ne mesure ni les tokens ni les coûts fournisseur. Les champs de revue
humaine sont initialisés à `null` : soutien factuel, absence de chiffres
inventés, utilité pédagogique. Les remplir après lecture des passages.
Les rapports sont locaux dans `.runtime/`, et un fichier existant n'est jamais
écrasé. Les rapports d'exécution restent locaux ; publier une synthèse datée
sans secrets après revue, en distinguant cas exécutés et cas non exécutés.
