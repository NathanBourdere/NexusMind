# Enrichir le corpus après le POC

Le tag GitHub [`POC`](https://github.com/NathanBourdere/NexusMind/tree/POC)
fige le commit `625b4fb0d49784b335d6215401ba34d9cb73d884` de `dev` :
Scout Data Dragon, retrieval, Coach Gemini gratuit, chat local et Analyste après
partie. Ce jalon désigne un POC utilisable, pas un coach expert ni une application
déployée. Les nouveaux connecteurs sont développés ensuite sur
`feat/knowledge-sources`. Voir l'[ADR-0009](decisions/0009-knowledge-sources.md).
Les [contrats des adaptateurs](source-connectors.md) et la
[validation datée](validation/knowledge-2026-11-01.md) complètent ce guide.

## Sources retenues et anciennes intégrations

Inspection du code et vérification d'accès du 1er novembre 2026 :

| Source | État dans le package maintenu | Apport et limite |
| --- | --- | --- |
| Riot Data Dragon | Déjà livré, inchangé | Descriptions versionnées des champions, objets, runes, sorts ; peu de macro |
| CommunityDragon RAW | Nouveau connecteur JSON testé en réel | Descriptions client, passif et sorts, dont texte dynamique ; pas de résolution des `@placeholders@`, ni de frame data reconstruite |
| Guide Riot « Comment jouer » | Nouveau connecteur testé en réel | Six chapitres : base, structures, jungle/objectifs, postes, économie, compétences ; introduction, pas de guide de freeze ou de macro avancée |
| Documents locaux attribués | Import JSON livré | Accueille des guides rédigés par le propriétaire ou des exports autorisés ; aucune licence ni qualité supposée à partir d'une URL |
| LoL Wiki actuel | Collecte désactivée | Le `robots.txt` exclut les robots d'IA et les chemins d'API ; demander un accès adapté avant toute intégration automatisée |
| LoLalytics | Ancien parser seulement | Aucun connecteur maintenu ni contrat d'API validé ici ; les signaux d'accès consultés ne constituent pas une autorisation générale d'ingestion RAG |
| Leaguepedia | Ancien parser seulement | Ancien endpoint Fandom refusé lors du contrôle ; la requête historique confond équipes et champions et ne produit pas un winrate fiable |
| Notes de patch Riot | À faire | Extracteur et correspondance des versions à tester séparément |

Le fichier historique `cdragon_parser.py` ne contenait qu'un commentaire.
Le Wiki utilisait Fandom et une rotation d'identités après `403` ; cette logique
n'est pas reprise. Les valeurs de camps écrites en dur et les `50 %` par défaut
des anciens parsers restent hors du package maintenu.

Les accès ont été vérifiés avec une identité explicite `NexusMind/0.1`, sans
connexion, abonnement ni navigateur automatisé. La collecte reste ciblée : pas de
crawl de liens. Une panne, un refus, un quota ou une redirection arrête la collecte,
sans changement d'identité ni retry automatique. Un `429` expose `Retry-After` ;
l'opérateur relance après ce délai. Les délais réseau sont `(5, 20)` secondes.

Références des fournisseurs : [CommunityDragon](https://www.communitydragon.org/docs),
[guide Riot](https://www.leagueoflegends.com/fr-fr/how-to-play/),
[robots Wiki](https://wiki.leagueoflegends.com/robots.txt),
[robots LoLalytics](https://lolalytics.com/robots.txt).
Ces accès peuvent évoluer ; les vérifications locales ne remplacent pas les
conditions de réutilisation du contenu.

## Collecter puis indexer

Les commandes sont distinctes pour inspecter les documents avant encodage.
Elles ne font aucun appel Gemini. Le guide Riot est actuellement français ;
CommunityDragon accepte `fr_FR` et `en_US` (répertoire `default` pour l'anglais).

```powershell
rtk proxy uv run --frozen nexusmind collect-knowledge --source riot-guide --source communitydragon --patch 16.21 --champion-id 103 --champion-id 81 --output .runtime/knowledge/articles.json
rtk proxy uv run --frozen nexusmind ingest-knowledge --input .runtime/knowledge/articles.json --data-dir .runtime --offline-model
rtk proxy uv run --frozen nexusmind retrieve "Pourquoi attaquer une tourelle avec des sbires ?" --patch 16.21.1 --data-dir .runtime --offline-model
rtk proxy uv run --frozen nexusmind retrieve "Décris le Q de Ahri" --corpus reference --patch 16.21.1 --data-dir .runtime --offline-model
```

`--champion-id` utilise l'identifiant numérique Riot, répétable ; au maximum
200 identifiants par collecte. Le patch CommunityDragon doit être fixé au format
`major.minor`, jamais `latest` ou `pbe`. Sans `--source`, seul le guide Riot est
collecté. Un fichier de collecte existant n'est pas écrasé. Une source en panne
empêche la création du fichier final ; aucun échec n'est masqué en corpus vide.

Arrêter le serveur avant d'écrire dans son Qdrant local, puis le redémarrer :
le runtime conserve le catalogue en mémoire. Pour des essais indépendants,
utiliser un autre `--data-dir`. Ne pas effacer un volume ou recréer une collection.
`--offline-model` exige que le modèle d'embeddings soit déjà téléchargé ; la
commande de collecte demande, elle, le réseau. Le [guide Scout](ingestion.md)
décrit les autres options de stockage.

## Importer un guide autorisé

`ingest-knowledge --input` attend une liste JSON de 1 à 200 `SourceArticle`
(fichier limité à 4 Mo). Les URL sont des métadonnées, jamais téléchargées par
l'importeur. Chaque article déclare :

| Champs | Usage |
| --- | --- |
| `source_id`, `source_key`, `source_name`, `source_url` | Fournisseur, identité stable du document, attribution lisible, URL HTTPS |
| `source_revision`, `retrieved_at` | Révision immuable et date ISO avec fuseau ; le hash des connecteurs identifie un contenu, pas une date de publication |
| `title`, `locale`, `patch` | Titre, langue réelle, patch réel ou `unversioned` si inconnu |
| `license_name`, `license_url`, `attribution` | Conditions déclarées et crédit conservés dans les passages et les citations |
| `topics` | Alias de sujets pour le routage lexical, par exemple `freeze` et `gestion de vague`, uniquement si couverts |
| `sections` | Objet `{titre: texte}` ; sections non vides, découpées avec leur titre |

La présence des champs n'établit pas les droits de réutilisation ni la justesse
du guide. Vérifier ces deux points avant import. Conserver ces fichiers dans
`.runtime/`, sans données personnelles. Pour un guide sans patch, ne pas lui
attribuer artificiellement le patch courant. Les exemples des tests sont
synthétiques et ne sont pas des conseils à importer.

## Retrieval et citations

`--corpus auto` est le mode par défaut du retrieval et du Coach. Il conserve
la priorité des fiches Riot pour les questions factuelles déjà couvertes, puis
consulte les références dont les sujets correspondent. `--corpus static`
restreint aux fiches Data Dragon ; `--corpus reference` sélectionne explicitement
les guides et données communautaires. Ces choix sont aussi disponibles dans le
chat et dans le champ JSON `corpus` de `/api/chat`.

Un nom de champion ne débloque pas à lui seul une question de freeze, gank ou
frame data. Les demandes de winrate, meilleur build, analyse de partie ou notes
de patch restent hors périmètre automatique. Le mode référence explicite ne
garantit pas que les passages répondent à toute la question : le Coach doit
s'abstenir si les preuves sont insuffisantes. Le routage est lexical et reste
une baseline, pas une vérification sémantique de l'exhaustivité des preuves.

La langue est filtrée exactement, sans traduction ou fallback implicite. Pour
une requête Data Dragon `16.21.1`, une référence `16.21` peut être sélectionnée,
avec mention de la différence de version. `16.20` est exclue. Une référence
`unversioned` reste non versionnée dans la réponse et fait apparaître une limite
d'actualité : ses chiffres ne sont pas certifiés pour le patch demandé.

Chaque passage de référence conserve nom, URL, hash/révision, langue, date,
conditions et attribution jusqu'au Coach et à l'affichage des sources. Les
passages Data Dragon existants gardent leurs identifiants et leur contenu.
Les nouveaux champs sont optionnels pour relire les anciens payloads ; les
références utilisent `schema_version=2`, avec le même modèle d'embeddings et la
même collection compatible. Aucune réindexation destructive n'est nécessaire.

Un rejeu identique garde les mêmes points. Les anciennes éditions restent
stockées ; seul le dernier article **entièrement indexé**, selon sa date de
collecte et à patch/langue identiques, est recherché. Une interruption avant
l'enregistrement du catalogue laisse l'édition précédente active. Une même
révision ne peut être réutilisée pour un texte différent. Le retour arrière
à une édition choisie et le nettoyage des vecteurs anciens n'ont pas encore de
commande dédiée. Ne pas confondre date de collecte et ordre éditorial des versions.

## Prochaine tranche utile

Écrire 20 questions concrètes de macro/micro (freeze, slow push, priorité,
recall, vision, objectifs, trade), identifier pour chacune les preuves absentes,
puis intégrer un petit ensemble de guides autorisés couvrant ces lacunes.
Évaluer les réponses et l'abstention avant d'augmenter le volume. CommunityDragon
enrichit les mécaniques décrites ; il ne remplace pas un corpus pédagogique.
Les statistiques de méta devront avoir leur propre pipeline avec échantillon,
patch, région, rang et taille de population explicites.
