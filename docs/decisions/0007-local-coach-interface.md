# 0007 — Interface locale et runtime persistant

Date : 2026-11-01
Statut : accepté

## Contexte

Le Coach est évalué et rapide, mais la CLI recharge l'encodeur à chaque
processus. Le propriétaire demande une interface de chat puis l'analyse
après partie, avant le déploiement cloud.

## Décision

Ajouter FastAPI/Uvicorn comme extra `web`, avec une page locale sans framework
frontend ni CDN. Le lifespan crée et ferme le runtime injecté une seule fois.
Les handlers réutilisent le Retriever, le Coach et la session HTTP, avec une
exécution exclusive et un budget de génération borné par processus.

Conserver l'écoute sur loopback, aucune persistance de conversations et
aucune collecte implicite. Les contrats du Coach et de l'index ne changent pas.
Le serveur ne recharge pas les documents pendant une session ; le redémarrer
après une ingestion. L'index Qdrant local reste à propriétaire unique.

## Conséquences

Le coût de chargement du modèle est payé au démarrage et non à chaque question.
Les tests remplacent le runtime sans réseau. L'extra et son lock sont installés
en CI. Un seul processus et une seule requête active suffisent au prototype.
Ce choix n'est pas une architecture publique multi-utilisateur : pas de quota
distribué ou d'authentification publique. Voir le [guide web](../web.md).

Référence : [lifespan FastAPI](https://fastapi.tiangolo.com/advanced/events/).
