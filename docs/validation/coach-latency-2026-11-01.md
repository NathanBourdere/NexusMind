# Réduction de latence du Coach — 1er novembre 2026

## Résultat mesuré

Le modèle par défaut devient `gemini-3.5-flash-lite`, raisonnement `MINIMAL`.
Les **cinq appels réels** ont tous retourné `answered`, en **1,27 à 2,10 s**,
avec une médiane observée de **1,85 s**. Ils couvrent quatre questions distinctes.
Le premier essai historique avec 3.8 Flash prenait **69,33 s** sur le Q d'Ahri ;
un nouvel appel de référence 3.8 a expiré après environ **90,26 s**.

| Étape | Question | Modèle | Durée | Résultat |
| --- | --- | --- | --- | --- |
| Référence historique | Q d'Ahri | 3.8 Flash / LOW | 69,326 s | Réponse |
| Exploration | Q d'Ahri | 3.5 Flash-Lite / MINIMAL | 2,087 s | Réponse |
| Exploration | Passif de Garen | 3.5 Flash-Lite / MINIMAL | 2,102 s | Réponse |
| Nouvelle référence | Q d'Ahri | 3.8 Flash / LOW | 90,263 s | Timeout |
| Profil implémenté | Q d'Ahri | 3.5 Flash-Lite / MINIMAL | 1,853 s | Réponse |
| Profil implémenté | Mur de Yasuo | 3.5 Flash-Lite / MINIMAL | 1,402 s | Réponse |
| Profil implémenté | Prix de l'Épée longue | 3.5 Flash-Lite / MINIMAL | 1,266 s | Réponse |

Le [rapport JSON](../../evaluation/reports/coach-latency-2026-11-01.json)
conserve les observations, modèles, tokens retournés par le fournisseur,
identifiants de citations et empreintes du corpus/de la suite, sans clé ou
contenu du `.env`. Les réponses complètes restent dans les rapports locaux
`.runtime/latency-*.json` du worktree Coach.

## Protocole et relecture

Les appels réutilisent les preuves du plan réel de 37 questions. Le prompt,
le schéma JSON, le contexte et le plafond de 2 048 tokens sont conservés.
Seuls le modèle et son profil de raisonnement changent. La durée couvre l'appel
et la validation applicative, hors retrieval et chargement de l'encodeur.
Aucun cache de réponse ni retry. Une session HTTP est réutilisée dans chaque
petit lot, et la première mesure rapide comprend sa première connexion.

L'agent a relu les cinq réponses contre les passages cités : trajets et types
de dégâts d'Ahri, régénération de Garen, durée du mur de Yasuo et prix de
350 pièces d'or de l'objet correspondent au texte Riot. Les références existent
et les exercices sont présents. Cette relecture n'est pas une validation
pédagogique humaine indépendante.

## Limites et reproductibilité

Ce petit échantillon de développement ne mesure pas une latence générale du
service gratuit, un p95 fiable ou une qualité équivalente sur toutes les questions.
Le timeout de référence est une observation censurée, pas une réponse de 90 s.
Ne pas calculer une médiane appariée ou attribuer le gain au seul raisonnement.

`coach` et `evaluate-coach` prennent le profil rapide par défaut. Ajouter
`--coach-model gemini-3.8-flash` pour reproduire l'ancien profil explicitement.
Voir le [guide](../coach.md) pour la clé gratuite, les budgets et les commandes.
Le [premier rapport Coach](coach-2026-11-01.md) conserve l'historique.

Le démarrage à froid de la CLI charge toujours l'encodeur : **1,85 s n'est pas
une mesure du temps total de lancement d'une nouvelle commande**. Une future
API persistante devra charger le modèle une fois et le réutiliser. Le corpus
et les données locales n'ont pas été réingérés ou migrés.

Vérifications : **89 tests hors ligne passent**, Ruff check et format check
passent. Les tests vérifient notamment le choix par défaut, les deux profils
de raisonnement, le choix explicite et le rejet d'un modèle inconnu avant réseau.
