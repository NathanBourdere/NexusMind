# Développement local

## État et préparation

Le projet utilise Python 3.12, `pyproject.toml` et `uv.lock`. Le chemin
`requirements.txt` de l'ancien README n'existe pas. Installer Python et uv selon
son environnement, puis travailler depuis la racine du dépôt.

Les exemples utilisent RTK selon l'instruction locale. Sans RTK, enlever le
préfixe `rtk proxy` ou `rtk` et conserver la commande sous-jacente.

```powershell
rtk git status --short --branch
rtk proxy uv --version
rtk proxy uv sync --frozen
rtk proxy uv run --frozen python --version
```

Ces commandes décrivent la préparation attendue ; l'installation n'a pas été
validée dans cet audit. `--frozen` conserve le lock existant. Une installation
réussie ne suffit pas encore à lancer Scout : `sentence-transformers` manque
dans les dépendances directes. Corriger cela dans la première tranche de la
[roadmap](roadmap.md), sans installation manuelle qui masquerait le problème.

## Démo actuelle

```powershell
rtk proxy uv run --frozen python main.py
```

Ne lancer cette démo qu'après correction des prérequis, avec Qdrant accessible
sur `http://localhost:6333`, accès réseau choisi et espace pour le modèle.
Elle télécharge potentiellement un encodeur, appelle encore les sources tierces
et écrit dans les collections locales. Ce n'est ni une commande hors ligne ni
le futur mode Riot uniquement. Aucun fichier Compose n'est actuellement fourni.

`.env` est ignoré par Git, mais sa présence ne configure pas automatiquement
l'application : le point d'entrée ne charge ni variables Riot ni fichier dotenv.
La configuration par environnement et un `.env.example` expurgé sont à introduire
avec des tests. Ne pas documenter une variable comme fonctionnelle avant cela.

## Conventions d'implémentation

- Typage des interfaces, validation Pydantic aux frontières, erreurs explicites.
- Fonctions courtes avec une responsabilité ; pas de refonte générale dans une correction ciblée.
- Aucun appel réseau à l'import ; injection des clients/encodeurs pour les tests.
- Fermer sessions et clients, y compris en cas d'erreur. Définir qui possède
  un client partagé pour éviter des fermetures multiples.
- Éviter I/O synchrone sur la boucle async ; mesurer et choisir une solution
  cohérente avant d'introduire davantage de concurrence.
- Respecter les unités : temps en secondes ou millisecondes explicitement
  convertis, dates UTC avec fuseau, ratios ou pourcentages nommés sans ambiguïté.
- Vérifier la casse des imports sur Linux. Un changement de casse de fichier
  sous Windows doit être enregistré par Git via un nom temporaire distinct.
- Toute dépendance directement importée doit être déclarée. Mettre à jour
  `pyproject.toml` et `uv.lock` ensemble ; ne pas modifier le lock à la main.

## Vérifier avant livraison

Exécuter les contrôles adaptés de [testing.md](testing.md), puis :

```powershell
rtk git diff --check
rtk git diff --stat
rtk git status --short
```

Pour une PR documentaire, vérifier tous les liens relatifs, distinguer les
commandes actuelles et futures et comparer les chemins avec les fichiers réels.
Pour le code, inclure les résultats des tests et signaler toute dépendance
externe empêchant un test d'intégration.
