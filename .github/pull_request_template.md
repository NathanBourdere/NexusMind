## Problème et comportement obtenu

Problème concret, résultat et critère d'acceptation. Lier l'issue.

## Validation

Commandes réellement exécutées, résultats, régression et contrôles non exécutés
avec leur raison. Pour la documentation seule : liens, chemins et cohérence.

## Données et livraison

Changements de source, patch, payload, embedding, dépendances ou configuration.
Migration/rollback si nécessaire, sinon « sans objet ».

## Avant revue

- [ ] Cible de branche correcte selon `docs/git-workflow.md`.
- [ ] Périmètre unique, commits atomiques et diff sans travail local étranger.
- [ ] Test rouge puis vert pour un comportement ajouté/corrigé, ou exception documentaire expliquée.
- [ ] Contrôles adaptés passés ; limites et dépendances externes explicites.
- [ ] Documentation et ADR actualisés si nécessaire.
- [ ] Aucun secret, log, volume Qdrant ou donnée personnelle dans le diff.
