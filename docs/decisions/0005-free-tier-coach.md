# 0005 — Coach injectable avec Gemini gratuit et appels bornés

Date : 2026-11-01
Statut : accepté pour le fournisseur ; déploiement cloud proposé

Le modèle par défaut est ensuite remplacé par le profil rapide de
l'[ADR-0006](0006-low-latency-coach.md). La décision ci-dessous conserve le
contexte du premier essai réussi avec 3.8 Flash.

## Contexte

Le retrieval est livré et mesuré. Le propriétaire demande le Coach avec un
budget strict de zéro euro et un futur hébergement cloud permettant d'apprendre
Kubernetes. Il accepte Gemini en offre gratuite. L'inférence d'un grand modèle
sur les ressources gratuites disponibles complique ce premier objectif.

## Décision

Implémenter un Coach applicatif indépendant du fournisseur et un adaptateur
REST Gemini `gemini-3.8-flash`, sans SDK supplémentaire. Réutiliser le Retriever
hors LLM. Un seul appel génère des affirmations structurées, leurs références,
un exercice et des limites. Vérifier les références par code, sans second LLM.
Le modèle peut s'abstenir même si le retrieval a retourné des passages.

L'essai du 1er novembre a révélé un HTTP 404 sur `gemini-2.5-flash` : ce modèle
n'est plus accessible aux nouveaux utilisateurs, bien que sa fiche soit encore
retournée par l'API. Le remplacement `gemini-3.8-flash` est indiqué par Gemini
et possède une offre gratuite vérifiée dans les tarifs officiels. Utiliser le
niveau de raisonnement `LOW`, sans fallback automatique vers un autre modèle.

Exiger une confirmation de projet sans facturation ; arrêter sur quota, sans
retry ni secours payant. Ne pas annoncer de garantie de coût indépendante du
compte fournisseur. Les bornes et commandes sont dans le [guide Coach](../coach.md).
Ne pas exposer un changement libre de modèle ou d'URL fournisseur en CLI.

Pour le cloud futur, proposer Docker puis K3s sur une VM Oracle Always Free
éligible. Cette piste n'est pas un déploiement réalisé ni une garantie de
capacité gratuite disponible. Le choix définitif sera revérifié au déploiement.

## Conséquences

Pas de GPU à héberger et aucune nouvelle dépendance Python. Contrats testables
hors ligne. En contrepartie : quotas et disponibilité externes, accès Internet,
conditions fournisseur et partage des questions avec Google.

Les citations valides ne garantissent pas l'exactitude des affirmations ; une
évaluation avec le modèle réel et une revue pédagogique restent requises.
Les limites du corpus Riot restent les mêmes. Pas de LangGraph, d'API publique,
de conversation persistante ni de déploiement Kubernetes dans cette tranche.

## Options examinées

- Groq gratuit : autre adaptateur possible, à comparer sur les mêmes questions
  si les quotas ou résultats Gemini ne conviennent pas.
- Modèle local : utile pour travailler hors ligne selon le matériel personnel ;
  hébergement d'inférence cloud gratuit moins simple à assurer.
- API payante ou GPU loué : incompatible avec le budget demandé.

Références vérifiées le 1er novembre 2026 :
[tarifs Gemini](https://ai.google.dev/gemini-api/docs/pricing),
[quotas Gemini](https://ai.google.dev/gemini-api/docs/rate-limits),
[Oracle Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm),
[ressources K3s](https://docs.k3s.io/installation/requirements).
