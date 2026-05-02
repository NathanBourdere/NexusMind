"""
Agent Scout - Agent d'exploration et de collecte de données
Premier agent du système multi-agents NexusMind
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from qdrant_client.async_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

# Import du parser principal
from data.parsers.main_parser import MainParser

# Import des schémas Pydantic
from core.schema.Champion import Champion
from core.schema.GameStateSnapshot import GameStateSnapshot
from core.schema.Matchup import Matchup
from core.schema.Summoner import Summoner


class ScoutAgent:
    """Agent Scout - Responsable de la collecte et de l'exploration des données"""

    def __init__(self, riot_api_key: Optional[str] = None, qdrant_url: str = "http://localhost:6333"):
        self.parser = MainParser(api_key=riot_api_key)
        self.agent_name = "Scout"
        self.agent_role = "Data Collection & Storage Specialist"
        self.agent_capabilities = [
            "Collecte de données de champions",
            "Analyse de matchups",
            "Surveillance de parties en direct",
            "Rapports de meta actuelle",
            "Profiling de joueurs",
            "Stockage RAG avec Qdrant",
            "Génération d'embeddings sémantiques"
        ]

        # Initialisation Qdrant ASYNCHRONE
        self.qdrant_client = AsyncQdrantClient(url=qdrant_url)
        self.collections = {
            'champions': 'nexusmind_champions',
            'matchups': 'nexusmind_matchups',
            'meta': 'nexusmind_meta',
            'players': 'nexusmind_players',
            'game_states': 'nexusmind_game_states'
        }

        # Initialisation du modèle d'embedding (SentenceTransformer)
        try:
            print("⏳ Scout: Chargement du modèle d'embedding (all-MiniLM-L6-v2)...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
            print(f"✅ Scout: Modèle chargé (Dimension: {self.vector_size})")
        except Exception as e:
            print(f"⚠️ Scout: Impossible de charger le modèle d'embedding: {e}")
            self.embedding_model = None
            self.vector_size = 384  # Taille par défaut de MiniLM

    # --- MÉTHODES D'INITIALISATION ASYNCHRONES ---

    async def initialize(self):
        """À appeler obligatoirement après la création de l'agent pour setup Qdrant"""
        await self._initialize_qdrant_collections()

    async def _initialize_qdrant_collections(self):
        """Initialise les collections Qdrant si elles n'existent pas"""
        try:
            for collection_name in self.collections.values():
                await self._create_collection_if_not_exists(collection_name, self.vector_size)
            print("✅ Scout: Collections Qdrant vérifiées/initialisées")
        except Exception as e:
            print(f"❌ Scout: Erreur lors de l'initialisation des collections Qdrant: {e}")

    async def _create_collection_if_not_exists(self, collection_name: str, vector_size: int):
        """Crée une collection Qdrant si elle n'existe pas de manière asynchrone"""
        try:
            # Qdrant Async nécessite 'await'
            collections_response = await self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections_response.collections]

            if collection_name not in collection_names:
                await self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                print(f"📁 Scout: Collection '{collection_name}' créée")
        except Exception as e:
            print(f"❌ Scout: Erreur lors de la création de la collection '{collection_name}': {e}")

    # --- GESTION DES VECTEURS ET DU RAG ---

    async def _generate_real_vector(self, text: str) -> List[float]:
        """Génère un vecteur sémantique sans bloquer l'Event Loop (Async)"""
        if not self.embedding_model:
            return [0.0] * self.vector_size

        loop = asyncio.get_event_loop()
        # run_in_executor empêche le calcul CPU du modèle de figer le serveur
        vector = await loop.run_in_executor(None, self.embedding_model.encode, text)
        return vector.tolist()

    async def _store_in_qdrant(self, collection_name: str, points: List[PointStruct]) -> bool:
        """Stocke des points dans Qdrant de manière asynchrone"""
        try:
            await self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"✅ Scout: {len(points)} point(s) stocké(s) dans '{collection_name}'")
            return True
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage dans '{collection_name}': {e}")
            return False

    async def _search_qdrant(self, collection_name: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche sémantique asynchrone dans Qdrant"""
        try:
            results = await self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            return [{'id': hit.id, 'score': hit.score, 'payload': hit.payload} for hit in results]
        except Exception as e:
            print(f"❌ Scout: Erreur lors de la recherche dans '{collection_name}': {e}")
            return []

    # --- MÉTHODES DE STOCKAGE TYPÉES (PYDANTIC) ---

    async def store_champion_data(self, champion: Champion) -> bool:
        """Stocke un objet Champion (Pydantic) dans Qdrant avec un vrai contexte sémantique"""
        try:
            # 1. Validation et dump Pydantic
            champ_dict = champion.model_dump()
            
            # 2. Création d'un texte riche pour l'embedding
            roles = ", ".join(champion.roles)
            context_text = f"Champion League of Legends: {champion.name}, {champion.title}. " \
                           f"Rôles: {roles}. Difficulté: {champion.difficulty}/10. " \
                           f"Passif: {champion.passive.name} - {champion.passive.description} " \
                           f"Conseils: {champion.summary or 'Aucun résumé'}"
            
            # 3. Génération du vecteur (Async)
            vector = await self._generate_real_vector(context_text)

            # 4. ID Déterministe (évite les doublons lors des mises à jour)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"champion_{champion.name}"))

            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    'data': champ_dict,
                    'timestamp': datetime.now().isoformat(),
                    'collection_type': 'champion',
                    'source': 'scout_agent'
                }
            )
            return await self._store_in_qdrant(self.collections['champions'], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage des données champion: {e}")
            return False

    async def store_game_state_data(self, game_state: GameStateSnapshot) -> bool:
        """Stocke un Snapshot de partie (Pydantic) dans Qdrant"""
        try:
            state_dict = game_state.model_dump()
            context_text = f"Game Snapshot ID {game_state.game_id} à {game_state.timestamp} secondes. " \
                           f"Différence de Gold: {game_state.gold_diff}."
            
            vector = await self._generate_real_vector(context_text)
            # Utilise le Game ID et le timestamp pour l'unicité
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"game_{game_state.game_id}_{game_state.timestamp}"))

            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    'data': state_dict,
                    'timestamp': datetime.now().isoformat(),
                    'collection_type': 'game_state'
                }
            )
            return await self._store_in_qdrant(self.collections['game_states'], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage du game_state: {e}")
            return False

    # (TODO) Remplacer Dict par les classes Matchup et Summoner quand elles seront instanciées par le parser
    async def store_generic_data(self, data: Dict[str, Any], collection_key: str, entity_name: str) -> bool:
        """Méthode de fallback pour les données non encore typées en Pydantic"""
        try:
            text_repr = json.dumps(data, sort_keys=True)
            vector = await self._generate_real_vector(text_repr[:1000]) # Limite pour l'embedding
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{collection_key}_{entity_name}"))

            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={'data': data, 'timestamp': datetime.now().isoformat()}
            )
            return await self._store_in_qdrant(self.collections[collection_key], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur stockage générique: {e}")
            return False

    # --- MISSIONS DE L'AGENT ---

    async def scout_champion(self, champion_name: str, role: str = "top", store_in_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Explore un champion spécifique et collecte toutes les données disponibles"""
        try:
            print(f"🔍 Scout: Exploration du champion {champion_name} (role: {role})...")

            # Le parser doit idéalement retourner une instance de Champion (Pydantic)
            champion_data = await self.parser.get_champion_expert_data(champion_name) # Adapter selon ta méthode du main_parser

            if not champion_data:
                return None

            # Si le parser retourne un dictionnaire, on le convertit en Champion (à adapter selon ton parser)
            if isinstance(champion_data, dict):
                champion_obj = Champion(**champion_data)
            else:
                champion_obj = champion_data

            analysis = self._analyze_champion_data(champion_obj.model_dump())

            report = {
                'agent': self.agent_name,
                'action': 'champion_scout',
                'target': champion_name,
                'timestamp': datetime.now().isoformat(),
                'data': champion_obj.model_dump(),
                'analysis': analysis
            }

            if store_in_rag:
                print(f"💾 Scout: Stockage des données de {champion_name} dans Qdrant...")
                await self.store_champion_data(champion_obj)

            print(f"✅ Scout: Exploration de {champion_name} terminée")
            return report
        except Exception as e:
            print(f"❌ Scout: Erreur lors de l'exploration de {champion_name}: {e}")
            return None

    async def scout_live_game(self, game_id: str, store_in_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Surveille une partie en cours via le Game ID"""
        try:
            print(f"🎮 Scout: Snapshot de la partie {game_id}...")
            
            # Récupère l'objet Pydantic GameStateSnapshot
            game_state_obj = await self.parser.get_full_game_context(game_id)
            
            if not game_state_obj:
                return None

            if store_in_rag:
                await self.store_game_state_data(game_state_obj)
                
            return {"status": "success", "data": game_state_obj.model_dump()}
        except Exception as e:
            print(f"❌ Scout: Erreur live game: {e}")
            return None

    # --- FONCTIONS D'ANALYSE (Logique interne) ---
    
    def _analyze_champion_data(self, champion_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse basique pour générer des insights immédiats"""
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'meta_position': ''
        }
        
        # Exemple d'analyse basée sur les stats Pydantic
        stats = champion_dict.get('stats', {})
        if stats.get('difficulty', 0) > 7:
            analysis['weaknesses'].append("Champion très mécanique, courbe d'apprentissage dure.")
            
        return analysis

    # --- OUTILS ADMIN ---

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de toutes les collections (Asynchrone)"""
        try:
            stats = {}
            for collection_name, collection_id in self.collections.items():
                try:
                    collection_info = await self.qdrant_client.get_collection(collection_id)
                    stats[collection_name] = {
                        'points_count': collection_info.points_count,
                        'vector_size': collection_info.config.params.vectors.size,
                        'status': collection_info.status
                    }
                except Exception as e:
                    stats[collection_name] = {'error': str(e)}

            return stats

        except Exception as e:
            print(f"❌ Scout: Erreur lors de la récupération des stats: {e}")
            return {}

    async def populate_rag_with_all_data(self, champions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Peuple le RAG avec toutes les données disponibles"""
        print("🚀 Scout: Démarrage du processus de peuplement RAG...")
        champions = champions or ["Aatrox", "Ahri", "Akali", "Yasuo", "Zed"]

        results = {'processed': 0, 'errors': []}

        for champion in champions:
            try:
                await self.scout_champion(champion, store_in_rag=True)
                results['processed'] += 1
            except Exception as e:
                results['errors'].append(f"{champion}: {e}")

        print(f"✅ Scout: Peuplement terminé. {results['processed']} insérés. Erreurs: {len(results['errors'])}")
        return results

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent"""
        return {
            'name': self.agent_name,
            'role': self.agent_role,
            'capabilities': self.agent_capabilities,
            'status': 'active',
            'collections': list(self.collections.values()),
            'vector_size': self.vector_size,
            'embedding_model': 'all-MiniLM-L6-v2' if self.embedding_model else 'not_loaded'
        }