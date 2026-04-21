# NexusMind

@@ -1 +1,59 @@
-# NexusMind+# NexusMind - Coach Multi-Agents pour LoL                                                                                                                                                            
+                                                                                                                                                                                                                 
+NexusMind est un projet visant à développer un assistant multi-agents pour le jeu League of Legends (LoL). L'objectif est de créer une intelligence artificielle capable d'aider les joueurs dans divers aspects 
du jeu, en utilisant des techniques d'apprentissage automatique et de traitement du langage naturel.                                                                                                              
+                                                                                                                                                                                                                 
+## Architecture du Projet                                                                                                                                                                                        
+                                                                                                                                                                                                                 
+Le projet est divisé en plusieurs phases pour permettre un développement progressif et structuré :                                                                                                               
+                                                                                                                                                                                                                 
+### Phase 1 : Fondations & Data (L'Agent "Scout")                                                                                                                                                                
+                                                                                                                                                                                                                 
+- **Setup API Riot** : Créer un compte sur le Riot Developer Portal et récupérer une clé API temporaire.                                                                                                         
+- **Script d'extraction** : Utiliser `requests` ou `RiotWatcher` pour récupérer le match_id de la dernière partie du joueur.                                                                                     
+- **Parsing JSON** : Extraire les stats clés (KDA, CS, Gold, Items, Vision Score) du fichier de match.                                                                                                           
+- **Anonymisation** : Créer une fonction pour nettoyer ces données et les rendre lisibles par un LLM (transformer les IDs en noms de champions/items).                                                           
+                                                                                                                                                                                                                 
+### Phase 2 : Connaissance Métier (Le Rerieval Augmented Generation - RAG)                                                                                                                                       
+                                                                                                                                                                                                                 
+- **Data Scraping** : Récupérer le texte du dernier "Patch Note" sur le site officiel de LoL.                                                                                                                    
+- **Vecteur Database** : Installer `chromadb` ou `faiss`.                                                                                                                                                        
+- **Chunking & Embedding** : Découper le patch note en petits morceaux et les transformer en vecteurs (via `sentence-transformers` ou l'API d'OpenAI).                                                           
+- **Test de recherche** : Faire une requête manuelle sur la base pour vérifier qu'elle renvoie bien les bons changements d'items quand on pose une question.                                                     
+                                                                                                                                                                                                                 
+### Phase 3 : Intelligence & SMA (Orchestration CrewAI)                                                                                                                                                          
+                                                                                                                                                                                                                 
+- **Configuration du LLM** : Installer `ollama` (pour un modèle local gratuit comme Llama 3) ou configurer une clé API Groq/OpenAI.                                                                              
+- **Définition de l'Agent Analyste** : Lui donner le rôle d'expert stats et l'accès aux données de la Phase 1.                                                                                                   
+- **Définition de l'Agent Meta** : Lui donner le rôle d'expert patch et l'accès à la Phase 2 (RAG).
+- **Définition de l'Agent Coach** : Lui donner le rôle de synthétiseur pédagogique.                                                                                                                              
+- **Protocole de communication** : Définir l'ordre des tâches (Séquentiel : Scout -> Meta -> Coach).                                                                                                             
+                                                                                                                                                                                                                 
+### Phase 4 : Interface & Démo                                                                                                                                                                                   
+                                                                                                                                                                                                                 
+- **Streamlit App** : Créer une page simple avec un champ pour entrer le pseudo (Summoner Name).                                                                                                                 
+- **Affichage des résultats** : Afficher les stats brutes d'un côté et le rapport final du SMA de l'autre.                                                                                                       
+- **Sidebar** : Ajouter des options pour choisir le patch ou le type de conseil (aggressif, safe, macro).                                                                                                        
+                                                                                                                                                                                                                 
+### Phase 5 : "Pro" & Déploiement                                                                                                                                                                                
+                                                                                                                                                                                                                 
+- **GitHub Clean-up** : Créer un README.md avec un schéma d'architecture.                                                                                                                                        
+- **Requirements** : Générer le fichier `requirements.txt`.                                                                                                                                                      
+- **Refactoring** : Vérifier que les clés API ne sont pas en clair dans le code (utiliser un `.env`).                                                                                                            
+                                                                                                                                                                                                                 
+## Installation et Exécution                                                                                                                                                                                     
+                                                                                                                                                                                                                 
+Pour exécuter ce projet, suivez ces étapes :                                                                                                                                                                     
+                                                                                                                                                                                                                 
+1. Clonez le dépôt sur votre machine.                                                                                                                                                                            
+2. Installez les dépendances en exécutant `pip install -r requirements.txt`.                                                                                                                                     
+3. Configurez les clés API nécessaires dans un fichier `.env` (voir la section "Phase 5").                                                                                                                       
+4. Exécutez le script principal avec `python main.py`.                                                                                                                                                           
+                                                                                                                                                                                                                 
+## Contribution                                                                                                                                                                                                  
+                                                                                                                                                                                                                 
+N'hésitez pas à contribuer au projet en soumettant des pull requests ou en créant des issues sur le dépôt GitHub.                                                                                                
+
+## Auteur
+
+Ce projet a été développé par [Votre Nom].
+