# 0003 — Un package Python installé et des adaptateurs explicites

Date : 2026-10-31
Statut : accepté dans le chantier Scout demandé par le propriétaire

## Contexte

Les dossiers historiques mélangent les responsabilités et utilisent des imports
sensibles à la casse. Le répertoire de travail principal contient des modifications
utilisateur non committées, à préserver. L'ingestion Riot doit être testée sans
importer les scrapers ni les schémas historiques encore incomplets.

## Décision

Le code maintenu et distribué est `src/nexusmind/`, installé par uv/Hatchling.
Le domaine contient documents et validation des vecteurs ; l'application contient
Scout et ses ports ; l'infrastructure implémente Riot, SQLite, Qdrant et les
embeddings. La CLI assemble et ferme les adaptateurs. Les tests restent hors du
package et les artefacts locaux dans `.runtime/`, ignoré par Git.

Le point d'entrée supporté est `nexusmind` ou `python -m nexusmind`. Les anciens
`agents/`, `core/`, `data/parsers/` et `main.py` restent conservés pour reprise
ultérieure ; ils ne sont ni importés ni distribués par le nouveau package. Il
s'agit d'une migration progressive, sans déplacer le travail local utilisateur.
Ne pas ajouter de nouvelles fonctionnalités dans ces anciens modules.

L'ingestion est synchrone et bornée : aucune boucle async n'est nécessaire pour
un premier worker séquentiel. Chaque lot indexe avant de valider les documents
dans SQLite. Les deux stockages n'ont pas de transaction distribuée : un rejeu
idempotent réconcilie les données après un échec partiel. Les anciennes collections
Qdrant restent intactes. Une collection dédiée est calculée depuis modèle,
révision, dimension, version du format et budget de tokens.

## Conséquences et validation

Installation indépendante du répertoire courant, imports sans I/O, tests de
transport et de normalisation hors ligne, intégration Qdrant isolée, rapport
persistant et échec visible. La recherche de contrôle récupère des passages ;
elle n'est pas encore un Coach LLM. Un retrait physique des dossiers historiques
nécessitera de réconcilier d'abord les modifications locales de leur propriétaire.
