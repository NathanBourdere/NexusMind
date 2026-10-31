# Git, GitHub et commits atomiques

## Branches

| Branche | Base | Cible de PR | Rôle |
| --- | --- | --- | --- |
| `main` | — | — | Versions stables et livrables |
| `dev` | `main` initialement | `main` pour une release | Intégration du prochain incrément |
| `feat/<sujet>` | `dev` | `dev` | Nouveau comportement |
| `fix/<sujet>` | `dev` | `dev` | Correction hors urgence production |
| `docs/<sujet>` | `dev` | `dev` | Documentation seule |
| `test/<sujet>` | `dev` | `dev` | Infrastructure ou couverture de tests |
| `refactor/<sujet>` | `dev` | `dev` | Réorganisation sans changement de comportement |
| `chore/<sujet>` | `dev` | `dev` | Outillage et maintenance |
| `hotfix/<sujet>` | `main` | `main`, puis report vers `dev` | Incident d'une version publiée |

Noms courts en anglais et kebab-case, par exemple `feat/riot-only-ingestion`.
Une branche correspond à une intention de PR. Aucun développement direct sur
`main` ou `dev`.

## Migration des branches historiques

L'audit a trouvé `develop`, pas `dev`, ainsi que `scout`, `parser` et `schema`.
Lors de la publication documentaire autorisée par le propriétaire, les références
distantes ont été synchronisées : aucune `dev` distante n'existait. La comparaison
`develop...scout` donnait 0 commit exclusif à `develop` et 17 à `scout`. `dev` a
donc été initialisée sur `scout` (`f3ee372`), sans inclure le travail non committé.
La contribution documentaire passe par `docs/project-foundations`, puis PR vers
`dev`. Les branches historiques sont conservées ; aucune protection distante
n'est créée implicitement par cette opération.

Pour poursuivre la migration des branches historiques, faire une opération dédiée :

1. Inventorier branches locales/distantes, PR ouvertes et commits non intégrés.
2. Depuis un arbre propre ou un worktree isolé, comparer `main`, `develop` et
   les branches historiques ; décider quels commits préserver et dans quel ordre.
3. Créer `dev` depuis la branche d'intégration retenue et porter les changements
   par PR revues, sans réécrire les branches partagées.
4. Adapter cibles de PR, filtres CI, protections et branche par défaut.
5. Archiver les anciennes branches uniquement après vérification de l'intégration.

Ne pas créer `dev` depuis `main` en supposant que `develop` n'a rien à conserver.
Ne pas supprimer une branche pour « nettoyer » pendant une autre tâche.

## Cycle d'une contribution après migration

Adapter les exemples et protéger le travail local avant tout changement de branche.

```powershell
rtk git status --short --branch
rtk git fetch origin
rtk git switch dev
rtk git pull --ff-only origin dev
rtk git switch -c fix/qdrant-collection-alias
```

Définir une issue ou un critère d'acceptation, tester puis implémenter.
Synchroniser au besoin avec `origin/dev` par merge ; réserver le rebase aux
commits locaux non partagés. Pas de force-push sur les branches partagées.
Ne jamais utiliser `reset --hard` pour résoudre du travail utilisateur.

## Commits atomiques

Format : `type(scope): imperative summary`, sujet anglais court. Types : `feat`,
`fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf`. Scope utile
comme `scout`, `rag`, `riot` ou `schema`. Pour une rupture, ajouter `!` et
expliquer `BREAKING CHANGE:` dans le corps avec la migration.

```text
fix(rag): resolve collection aliases before querying
feat(scout): support Riot-only ingestion
docs: define contribution and release workflow
```

Un commit a une raison unique et doit pouvoir être annulé sans dommage
collatéral. Regrouper test et implémentation du même comportement. Le test rouge
est observé localement ; il n'impose pas un commit cassé. Inclure la documentation
du contrat changé et le lock nécessaire. Séparer formatage massif, fonctionnalité
et correction sans lien.

Avant chaque commit autorisé :

```powershell
rtk git diff
rtk git add -p
rtk git diff --cached --check
rtk git diff --cached
rtk git status --short
rtk git commit -m "fix(rag): resolve collection aliases before querying"
```

Pour un fichier neuf, `git add <chemin>` explicitement. Lire suppressions, secrets
et fichiers générés dans le diff indexé. Aucun `git add .` aveugle. Ne pas
embarquer les modifications préexistantes. Une demande d'édition n'est pas une
demande de commit, push, merge ou modification des paramètres distants.

## Pull requests et GitHub

Utiliser le [modèle de PR](../.github/pull_request_template.md). Décrire problème,
comportement final, tests, limites et migration. Une PR doit rester relisible ;
l'ouvrir en brouillon si des contrôles restent incomplets. Utiliser `Closes #N`
seulement si l'issue est entièrement résolue.

Configuration recommandée à appliquer séparément sur GitHub :

- Branche par défaut `main`, PR de travail ciblant explicitement `dev`.
- Protections/rulesets pour `main` et `dev` : PR obligatoire, discussions résolues,
  contrôles requis une fois la CI créée, blocage des suppressions et force-push.
- Relecture externe si disponible ; en solo, auto-revue explicite et CI sans
  imposer une approbation externe impossible à obtenir.
- Ne pas exiger de contrôle inexistant. Consigner les noms réels des jobs quand
  la CI est ajoutée. La documentation ne configure pas GitHub.
- Merge des PR de travail par **merge commit**, après contrôle des commits
  atomiques. Nettoyer les commits WIP avant partage ou reconstruire une PR propre
  sans réécriture des branches partagées.
- Release `dev` vers `main` par merge commit pour conserver l'ascendance et
  éviter les différences récurrentes entre branches permanentes.

Utiliser les modèles [feature](../.github/ISSUE_TEMPLATE/feature.md) et
[bug](../.github/ISSUE_TEMPLATE/bug.md). Labels suggérés : `feature`, `bug`,
`documentation`, `tests`, `data`, `rag`, `deployment`, puis une priorité.

## Releases et hotfix

Préparer une PR `dev` vers `main` : version du projet et lock cohérents, notes de
release, contrôles verts, état du corpus et procédure de retour arrière. Après
merge, créer un tag `vMAJOR.MINOR.PATCH` sur le commit livré : PATCH pour correction
compatible, MINOR pour fonctionnalité compatible, MAJOR pour rupture. Durant
`0.x`, expliquer explicitement toute rupture.

Un hotfix repart du commit stable de `main`, inclut son test de régression,
passe par PR vers `main`, puis est reporté vers `dev` par PR. Vérifier les deux
branches pour éviter de réintroduire le bug. Déployer l'artefact lié au tag et
consigner image, configuration et version du corpus.
