# TDD et évaluation du RAG

## Red / Green / Refactor

1. Choisir un comportement observable : par exemple résolution de `champions`
   en `nexusmind_champions` avant l'appel Qdrant.
2. Écrire le test avec un client simulé et une assertion sur le contrat public.
3. Observer un échec lié au comportement absent. Un import cassé ou une dépendance
   manquante n'est pas la preuve du bon test rouge.
4. Implémenter le minimum puis observer le vert.
5. Refactorer avec les tests verts, exécuter la suite pertinente et livrer test
   et implémentation ensemble. Conserver commandes et résultats dans la PR.

Une correction commence par une reproduction automatisée. Pour une exploration,
limiter le prototype puis stabiliser ses contrats par tests avant intégration.
Une modification documentaire requiert liens et cohérence, sans test artificiel
du contenu exact des phrases.

## Outillage disponible

Le package maintenu dispose de Pytest et Ruff dans le groupe `dev`, avec
configuration et lock. La pipeline est synchrone ; pytest-asyncio n'est donc pas
nécessaire. Les tests sont dans `tests/`, avec marqueur `integration` pour le
roundtrip Qdrant en mémoire. Les commandes exécutables sont :

```powershell
rtk proxy uv run --frozen pytest -q
rtk proxy uv run --frozen ruff check src tests
rtk proxy uv run --frozen ruff format --check src tests
rtk proxy uv run --frozen pytest -m integration
```

La mesure de retrieval existe via `nexusmind evaluate` : voir le
[protocole](retrieval.md). La CI ne charge pas le modèle ; elle vérifie les
métriques sur exemples manuels, les contrats et l'intégrité suite/rapport.
Les tests live restent à créer. Documenter les variables et fixtures réellement
nécessaires aux intégrations. Aucun appel live dans le contrôle obligatoire d'une PR.

| Niveau / emplacement cible | Ce qu'il prouve | Ressources |
| --- | --- | --- |
| `tests/unit/` | Normalisation, schémas, contexte, mapping et erreurs | Fixtures et doubles, aucune connexion |
| `tests/integration/`, marqueur `integration` | Filtres Qdrant, upsert, roundtrip et contrat client | Instance ou mode mémoire isolé ; encodeur déterministe |
| Marqueur `live` | Compatibilité avec une source réelle | Exécution volontaire, clé hors CI des PR et quotas bornés |
| `tests/evaluation/`, marqueur `evaluation` | Pertinence retrieval et qualité pédagogique | Corpus/questions versionnés, modèle fixé et budgets explicites |

Ne jamais utiliser les collections personnelles pour les tests. Créer un nom
temporaire unique et nettoyer uniquement les ressources du test. Le mode mémoire
Qdrant ne remplace pas tous les contrôles sur serveur réel.

## Premiers scénarios utiles

- Parser une fixture Data Dragon valide, valeur optionnelle absente, HTML et
  tooltip non résolu. Une absence n'est pas un zéro observé.
- Vérifier que l'ingestion Riot uniquement n'instancie ni n'appelle de fournisseur tiers.
- Simuler timeout, `401`/`403`, `404`, `429` avec `Retry-After`, `5xx` et limite
  des retries. Injecter horloge/sommeil pour des tests rapides.
- Rejouer deux fois un lot : même nombre de points. Changer patch ou langue :
  identités distinctes et filtre correct.
- Échec d'encodeur : aucune écriture de vecteur nul, erreur explicite.
- Vérifier alias de collections, filtres scalaires/listes, collection inconnue
  et résultat vide sur le contrat Qdrant.
- Une question sur un sort conserve le passage jusqu'au Coach ; les citations
  proviennent des documents récupérés.
- Imports sans réseau sous Linux, dont la casse de `Champion`.

Tester effets et contrats, sans recopier les constantes de l'implémentation ni
verrouiller le texte complet d'une réponse LLM.

## Évaluer avant d'ajouter de la complexité

Créer au moins 20 questions couvrant champions, sorts, objets, patchs, français
et sujets hors corpus. Stocker passages attendus, patch, faits requis, critères
de citation et cas d'abstention. Garder des questions de validation distinctes
de celles utilisées pour régler le pipeline.

Mesurer séparément :

- Retrieval : Recall@5, MRR et erreurs de patch/langue sur passages annotés.
- Génération : faits soutenus par citations, absence de chiffre inventé,
  abstention appropriée et utilité de l'explication/exercice.
- Exécution : latence médiane/p95, appels externes, tokens et coût éventuel.

Fixer corpus, modèle/révision, configuration et date des mesures. Une similarité
cosinus n'est pas une confiance calibrée. Établir la baseline puis consigner les
seuils de non-régression dans un ADR avant de bloquer une release sur ces scores.
Exiger dès le départ zéro citation inventée dans le jeu de validation et
l'abstention pour tous ses cas explicitement hors corpus. Revue humaine pour
la pédagogie ; un éventuel juge LLM ne suffit pas à lui seul.
