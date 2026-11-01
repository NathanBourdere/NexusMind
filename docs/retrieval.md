# Retrieval structuré et baseline

Les mesures de cette baseline portent sur le corpus statique du POC. L'extension
[multi-source](knowledge-sources.md) ajoute le choix `--corpus auto|static|reference`,
des concepts avec révision et attribution et un routage documentaire. Les scores
de la baseline ne mesurent pas la qualité du corpus pédagogique supplémentaire.

Le parcours maintenu ajoute deux commandes : `retrieve` retourne des passages
structurés ou une abstention, `evaluate` compare ce parcours à la recherche
vectorielle brute. Aucun LLM de génération n'intervient. Le Scout et l'index
existant restent compatibles ; aucune réingestion n'est nécessaire.

## Utilisation

Depuis la racine du checkout, avec le corpus déjà ingéré :

```powershell
rtk proxy uv run --frozen nexusmind retrieve "Décris le passif de Ahri" --patch 16.21.1 --offline-model
rtk proxy uv run --frozen nexusmind retrieve "Décris le Sablier de Zhonya" --patch 16.21.1 --entity-type item --entity-id 3157 --offline-model
rtk proxy uv run --frozen nexusmind retrieve "Comment freeze une vague avec Ahri ?" --patch 16.21.1 --offline-model
```

Les options communes `--data-dir`, `--qdrant-url`, `--model`, `--revision` et
`--model-cache` gardent le sens décrit dans le [guide Scout](ingestion.md).
Le modèle est construit avant le routage CLI : même une abstention peut donc
nécessiter son chargement initial. `--offline-model` requiert ses poids en cache.

`--entity-type` sélectionne `champion`, `item`, `rune` ou `summoner_spell`.
`--entity-id` peut être répété, avec au plus dix IDs d'un même type. Les IDs
doivent être présents dans le patch et la langue demandés ; aucun fallback
vers un autre patch ou une autre variante. Les comparaisons détectées sans
filtres explicites demandent une clarification. Un filtre contredisant le nom
détecté dans la question ne doit pas retourner les faits d'une autre entité.

`--section passive` ou `--section spell:AhriE` sélectionne une famille de
passages, y compris ses éventuels fragments `:chunk:N`. Sans section explicite,
le retriever reconnaît les noms complets de sorts/passifs présents dans le
corpus et les demandes de passif, classe ou sorts. Les raccourcis Q/W/E/R ne
sont reconnus que si l'ID Riot permet de les identifier sans inventer de mapping ;
privilégier le nom complet ou l'ID de section pour les autres cas.

## Résultat et responsabilités

| Champ | Signification |
| --- | --- |
| `status` | `ok`, `no_results`, `needs_clarification`, `out_of_scope` ou `unavailable` |
| `filters` | Type, IDs canoniques et sections effectivement sélectionnés |
| `passages` | ID, texte, provenance, patch/langue, hash, modèle/révision et score |
| `candidates` | IDs/types candidats lorsque le nom est ambigu |
| `limitations` | Périmètre statique, score non probabiliste et raison d'une abstention |
| `collection`, `elapsed_ms` | Index utilisé et durée du cas d'usage, hors chargement des clients |
| `error_type` | Type d'erreur technique pour `unavailable`, distinct d'un résultat vide |

`ok` signifie que des candidats ont été récupérés, pas que toute la question
est couverte ou que leur contenu répond correctement à chaque sous-question.
Le futur Coach doit vérifier ce soutien avant de rédiger. Aucune réponse ni
confiance de vérité n'est générée ici. `unavailable` retourne un code CLI non
nul ; les abstentions explicites sont des résultats normaux.

Les noms proviennent du format des passages v1, avec normalisation de casse,
accents et ponctuation. Les noms contenus dans un nom plus long ne créent pas
une fausse ambiguïté. Les variantes d'objets ou de sorts d'invocateur partageant
un même nom restent distinctes : fournir un ID ou demander un contexte de mode.
Les abréviations et fautes de frappe non reconnues conduisent à une clarification.

Le refus du coaching, des winrates, des matchs et d'autres intentions non
couvertes est une **liste lexicale limitée**, pas un classifieur universel ni
une preuve d'absence dans le corpus. Une formulation inconnue peut encore
passer ce filtre. Cette limite impose un contrôle de soutien côté Coach.

`search` reste un outil bas niveau renvoyant une liste : il accepte désormais
`--entity-type`, `--entity-id` répété et `--section` répété (valeurs exactes),
mais n'effectue pas le routage ou les abstentions de `retrieve`.

## Évaluation reproductible

```powershell
rtk proxy uv run --frozen nexusmind evaluate --suite evaluation/retrieval-v1.json --output .runtime/retrieval-report.json --offline-model
```

Préparer le corpus `16.21.1/fr_FR` et utiliser un snapshot isolé via `--data-dir`
pour reproduire une mesure sans toucher aux données principales. La suite et
le rapport sont fournis dans la distribution source ; pour une installation
wheel seule, passer explicitement un fichier de suite accessible avec `--suite`.
L'évaluation lit le corpus et ne le réingère pas.

La [suite annotée](../evaluation/retrieval-v1.json) couvre champions, sorts,
objets, runes, sorts d'invocateur, ambiguïtés, coaching, patch et langue absents.
Elle contient 37 cas : 24 positifs et 13 négatifs, avec des groupes development
et validation. Cinq demandes positives précisent un ID pour lever une ambiguïté ;
les mêmes questions sans cet ID sont aussi testées. Les résultats automatiques
et les filtres explicites sont rapportés séparément.

Les annotations visent des entités/sections, pas des réponses inventées. Les
IDs de passages attendus sont résolus dans le catalogue ; si une annotation
positive n'existe pas dans ce snapshot, l'évaluation échoue au lieu de l'ignorer.
Une panne du backend interrompt également la mesure. Aucun cas n'est supprimé
pour améliorer les scores.

Le rapport JSON comprend tous les cas, les IDs attendus/retrouvés, statuts,
filtres, métriques par groupe, empreintes de la suite et du corpus, versions du
modèle et de l'environnement. Recall@5 est la fraction des passages attendus
retrouvés, moyennée par question positive ; MRR@5 mesure le rang du premier
passage pertinent. L'abstention exige le bon statut **et** aucun passage pour
un cas négatif. Les latences excluent le chargement du modèle et le catalogue ;
la baseline est exécutée en premier pour chaque cas, ce qui limite la comparaison.

Voir la [validation datée](validation/retrieval-2026-10-31.md) et le
[rapport complet](../evaluation/reports/riot-static-fr-v1.json).
