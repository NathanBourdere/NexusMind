# Mesure du retrieval — 31 octobre 2026

Mesure du 31 octobre, finalisation le 1er novembre 2026. Le
[rapport complet](../../evaluation/reports/riot-static-fr-v1.json) et la
[suite annotée](../../evaluation/retrieval-v1.json) sont versionnés ensemble.

## Protocole

Snapshot isolé des 2 551 passages Riot `16.21.1/fr_FR`, sans réingestion ni
modification de l'index principal. Même modèle/révision que Scout. La baseline
filtre seulement patch/langue ; le nouveau parcours ajoute lookup de noms,
filtres d'entité/section, clarification et refus de certaines intentions.

37 cas : 24 positifs et 13 négatifs, groupes development (18) et validation (19).
Cinq positifs précisent un ID car plusieurs variantes partagent leur nom ; les
cinq mêmes questions sans ID sont aussi testées. Les autres cas couvrent des
compétences, runes, coaching, patch absent et langue absente.

Empreinte du corpus :
`cc7ba1bc754d167d6151263a0d06ba6beb8b73f0cfac1bb0c2399919fe57c336`.
Empreinte de la suite :
`7eaf1a8e665826a2c68329cdef10e3174e34e6f83b48e970898408c54f127c27`.
Le rapport conserve versions du modèle/environnement et tous les IDs attendus
et retrouvés, sans texte du corpus ni secret.

## Résultats

| Ensemble des cas | Recherche brute | Retrieval filtré |
| --- | ---: | ---: |
| Recall@5, 24 positifs | 12,5 % | 100 % |
| MRR@5 | 0,0660 | 0,9722 |
| Statut et abstention corrects, 13 négatifs | 2/13 | 13/13 |
| Passages d'une mauvaise entité, positifs | 110 | 0 |
| Erreurs de patch/langue | 0 | 0 |
| Latence médiane hors initialisation | 168 ms | 359 ms |
| Latence p95 hors initialisation | 653 ms | 471 ms |

Pour les 19 positifs sans ID explicite : Recall@5 de 15,8 % à 100 %, MRR@5 de
0,0833 à 0,9649. Les cinq cas avec ID sont rapportés séparément et atteignent
Recall@5/MRR@5 de 1 dans le parcours filtré. Les tableaux par groupe sont dans
le JSON. Recall@5 moyenne la fraction des passages attendus ; une section peut
contenir plusieurs fragments. MRR@5 utilise le premier pertinent dans le top 5.
Un négatif exige le bon statut et zéro passage.

## Limites

La mesure combine lookup, filtres et ranking ; elle ne prouve pas une amélioration
de l'encodeur seul. Le jeu est petit et rédigé par le même auteur que le code.
Les ambiguïtés ont été auditées pendant sa construction ; le groupe validation
est organisationnel, pas indépendant ou aveugle. Ajouter paraphrases et revue
humaine indépendante avant de fixer un seuil général de qualité.

Ces chiffres ne valident ni la vérité d'une réponse LLM ni la pédagogie. Le refus
lexical peut manquer des formulations nouvelles. Abréviations, fautes de frappe
et mapping complet des slots Q/W/E/R ne sont pas couverts. Le futur Coach doit
vérifier que chaque affirmation est soutenue par les preuves.

Le routage ajoute un coût médian observé. Il s'agit d'une mesure locale unique,
baseline exécutée en premier par cas, sans contrôle statistique. Le chargement
du modèle et la lecture du catalogue sont exclus. Aucun seuil cosinus n'a été
ajusté et aucun cas manquant n'a été retiré pour améliorer les scores.
La CI vérifie le code et l'intégrité de la suite, sans relancer le modèle réel.
Le serveur Qdrant distant reste hors validation réelle.
