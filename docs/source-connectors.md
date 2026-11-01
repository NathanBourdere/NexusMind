# Adaptateurs de connaissances publiques

Les nouveaux adaptateurs sont dans
`src/nexusmind/infrastructure/knowledge_sources.py`. Ils n'importent aucun parser
historique et ne chargent ni embeddings, ni Qdrant, ni LLM.

- `CommunityDragonSource.collect(patch=..., locale=..., champions=[...])` : JSON
  client, patch `major.minor` explicite, identifiants numériques Riot, français
  ou anglais. Le répertoire anglais est `default`. Conserve les descriptions
  dynamiques non résolues ; ne convertit pas leurs coefficients en statistiques.
- `RiotGuideSource.collect()` : six chapitres explicitement retenus du guide
  français Riot. L'extraction lit les données JSON embarquées, y compris les
  onglets absents du HTML visible initial. Le marketing est exclu.
- `import_articles(path)` : lit uniquement un fichier local, valide tous ses
  `SourceArticle` et ne télécharge pas les URL déclarées.
- `WikiSource.collect(...)` : refuse sans requête réseau ; source désactivée.

Chaque source réseau accepte une session injectée pour les tests. L'appelant
ferme `close()` ; une session fournie par l'appelant reste sous sa responsabilité.
L'identité est explicite, les accès sont ciblés, les redirections sont refusées
et les délais bornés. Un refus HTTP, un quota ou un refus robots interrompt le
parcours sans retry ni changement d'identité. Aucun lien de page n'est suivi.

Le contrat de domaine `SourceArticle` exige identité du fournisseur et du
document, révision, URL, titre, langue, patch réel ou `unversioned`, date avec
fuseau, conditions déclarées, attribution, sujets et sections non vides.
`documents()` produit des concepts révisionnés, avec les mêmes métadonnées et
des identifiants déterministes. Ces champs déclaratifs ne certifient ni les
droits ni la qualité pédagogique. Les anciens documents Data Dragon restent
lisibles et conservent leurs identifiants.

Les tests utilisent exclusivement des réponses HTTP synthétiques, couvrent
provenance, extraction, refus et validation d'import. Les règles générales de
qualité restent dans [Sources et provenance](data-sources.md).
