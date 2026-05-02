"""
Agent RAG - Retrieval Augmented Generation
Gère la recherche, le reranking et la génération de réponses depuis le RAG
"""

import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from qdrant_client.async_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer


@dataclass
class RetrievalResult:
    """Résultat d'une recherche RAG"""
    id: str
    score: float
    payload: Dict[str, Any]
    content: str
    source: str
    relevance: float = 0.0


@dataclass
class RAGResponse:
    """Réponse générée par l'agent RAG"""
    query: str
    answer: str
    sources: List[str]
    confidence: float
    context_used: List[str]
    metadata: Dict[str, Any]


class RAGAgent:
    """Agent RAG - Responsable du retrieval, reranking et génération de réponses"""

    def __init__(self, qdrant_url: str = "http://localhost:6333", model_name: str = "all-MiniLM-L6-v2"):
        self.agent_name = "RAG"
        self.agent_role = "Retrieval & Response Generation"
        self.agent_capabilities = [
            "Recherche vectorielle dans Qdrant",
            "Reranking des résultats",
            "Génération de réponses contextuelles",
            "Citation des sources",
            "Gestion du contexte et de la mémoire",
            "Optimisation des requêtes"
        ]

        # Initialisation Qdrant
        self.qdrant_client = AsyncQdrantClient(url=qdrant_url)
        self.collections = {
            'champions': 'nexusmind_champions',
            'matchups': 'nexusmind_matchups',
            'meta': 'nexusmind_meta',
            'players': 'nexusmind_players',
            'game_states': 'nexusmind_game_states'
        }

        # Initialisation du modèle d'embedding
        try:
            print("⏳ RAG: Chargement du modèle d'embedding...")
            self.embedding_model = SentenceTransformer(model_name)
            self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
            print(f"✅ RAG: Modèle chargé (Dimension: {self.vector_size})")
        except Exception as e:
            print(f"⚠️ RAG: Impossible de charger le modèle: {e}")
            self.embedding_model = None
            self.vector_size = 384

        # Configuration du reranking
        self.reranking_enabled = True
        self.max_results = 10
        self.top_k_results = 5

    async def initialize(self) -> None:
        """Initialise l'agent RAG"""
        try:
            print("🔄 RAG: Vérification des collections Qdrant...")
            collections_response = await self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections_response.collections]

            for collection_name in self.collections.values():
                if collection_name not in collection_names:
                    print(f"⚠️ RAG: Collection '{collection_name}' non trouvée")
                else:
                    print(f"✅ RAG: Collection '{collection_name}' disponible")

            print("✅ RAG: Initialisation terminée")
        except Exception as e:
            print(f"❌ RAG: Erreur lors de l'initialisation: {e}")

    async def _generate_query_vector(self, query: str) -> List[float]:
        """Génère un vecteur pour la requête"""
        if not self.embedding_model:
            return [0.0] * self.vector_size

        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(None, self.embedding_model.encode, query)
        return vector.tolist()

    async def search(self, query: str, collection_name: str = 'champions',
                    limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[RetrievalResult]:
        """Effectue une recherche dans le RAG"""
        try:
            print(f"🔍 RAG: Recherche '{query}' dans '{collection_name}'...")

            # Générer le vecteur de requête
            query_vector = await self._generate_query_vector(query)

            # Construire les filtres si fournis
            qdrant_filters = None
            if filters:
                qdrant_filters = self._build_filters(filters)

            # Effectuer la recherche
            results = await self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filters,
                limit=limit
            )

            # Convertir les résultats
            retrieval_results = []
            for hit in results:
                result = RetrievalResult(
                    id=str(hit.id),
                    score=hit.score,
                    payload=hit.payload,
                    content=self._extract_content(hit.payload),
                    source=hit.payload.get('source', 'unknown'),
                    relevance=hit.score
                )
                retrieval_results.append(result)

            print(f"✅ RAG: {len(retrieval_results)} résultats trouvés")
            return retrieval_results

        except Exception as e:
            print(f"❌ RAG: Erreur lors de la recherche: {e}")
            return []

    def _build_filters(self, filters: Dict[str, Any]) -> Filter:
        """Construit les filtres Qdrant"""
        conditions = []

        for field, value in filters.items():
            if isinstance(value, list):
                # Filtre avec plusieurs valeurs
                conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(any=value)
                    )
                )
            else:
                # Filtre avec une seule valeur
                conditions.append(
                    FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    )
                )

        return Filter(must=conditions)

    def _extract_content(self, payload: Dict[str, Any]) -> str:
        """Extrait le contenu textuel depuis le payload"""
        data = payload.get('data', {})

        # Extraire le contenu selon le type de données
        if 'name' in data:
            content = f"Champion: {data['name']}"
            if 'title' in data:
                content += f", {data['title']}"
            if 'summary' in data:
                content += f". {data['summary']}"
            return content

        elif 'champion1_name' in data and 'champion2_name' in data:
            return f"Matchup: {data['champion1_name']} vs {data['champion2_name']}"

        elif 'game_id' in data:
            return f"Game State: {data['game_id']}"

        return str(data)

    async def rerank_results(self, results: List[RetrievalResult], query: str) -> List[RetrievalResult]:
        """Rerank les résultats en fonction de la pertinence"""
        if not self.reranking_enabled or len(results) <= 1:
            return results

        try:
            print(f"🔄 RAG: Reranking de {len(results)} résultats...")

            # Générer le vecteur de la requête
            query_vector = await self._generate_query_vector(query)

            # Calculer la similarité sémantique avec chaque résultat
            for result in results:
                # Extraire le contenu du résultat
                result_content = result.content

                # Générer le vecteur du contenu
                loop = asyncio.get_event_loop()
                content_vector = await loop.run_in_executor(
                    None,
                    self.embedding_model.encode,
                    result_content
                )

                # Calculer la similarité cosinus
                similarity = self._cosine_similarity(query_vector, content_vector.tolist())
                result.relevance = similarity

            # Trier par pertinence
            reranked = sorted(results, key=lambda x: x.relevance, reverse=True)

            print(f"✅ RAG: Reranking terminé")
            return reranked[:self.top_k_results]

        except Exception as e:
            print(f"❌ RAG: Erreur lors du reranking: {e}")
            return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        try:
            import numpy as np
            vec1_array = np.array(vec1)
            vec2_array = np.array(vec2)

            dot_product = np.dot(vec1_array, vec2_array)
            norm1 = np.linalg.norm(vec1_array)
            norm2 = np.linalg.norm(vec2_array)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0

    async def generate_response(self, query: str, context: List[RetrievalResult],
                              max_context_length: int = 2000) -> RAGResponse:
        """Génère une réponse basée sur le contexte récupéré"""
        try:
            print(f"💬 RAG: Génération de réponse pour '{query}'...")

            # Sélectionner et formater le contexte
            selected_context = self._select_context(context, max_context_length)

            # Construire la réponse
            answer = self._construct_answer(query, selected_context)

            # Extraire les sources
            sources = [result.source for result in selected_context]

            # Calculer la confiance
            confidence = self._calculate_confidence(selected_context)

            response = RAGResponse(
                query=query,
                answer=answer,
                sources=sources,
                confidence=confidence,
                context_used=[result.id for result in selected_context],
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'results_count': len(context),
                    'context_length': len(selected_context),
                    'reranking_enabled': self.reranking_enabled
                }
            )

            print(f"✅ RAG: Réponse générée (confiance: {confidence:.2f})")
            return response

        except Exception as e:
            print(f"❌ RAG: Erreur lors de la génération de réponse: {e}")
            return RAGResponse(
                query=query,
                answer="Désolé, je n'ai pas pu générer de réponse.",
                sources=[],
                confidence=0.0,
                context_used=[],
                metadata={'error': str(e)}
            )

    def _select_context(self, results: List[RetrievalResult], max_length: int) -> List[RetrievalResult]:
        """Sélectionne le contexte optimal"""
        selected = []
        current_length = 0

        for result in results:
            content_length = len(result.content)
            if current_length + content_length <= max_length:
                selected.append(result)
                current_length += content_length
            else:
                break

        return selected

    def _construct_answer(self, query: str, context: List[RetrievalResult]) -> str:
        """Construit une réponse basée sur le contexte"""
        if not context:
            return "Je n'ai pas trouvé d'informations pertinentes pour répondre à votre question."

        # Formater la réponse
        answer_parts = [f"Basé sur {len(context)} source(s) trouvée(s):"]

        for i, result in enumerate(context, 1):
            source = result.source
            content = result.content
            relevance = result.relevance

            answer_parts.append(f"\n{i}. {source} (pertinence: {relevance:.2f}):")
            answer_parts.append(f"   {content}")

        answer_parts.append("\n\nSources:")
        for result in context:
            answer_parts.append(f"- {result.source}")

        return "\n".join(answer_parts)

    def _calculate_confidence(self, context: List[RetrievalResult]) -> float:
        """Calcule la confiance de la réponse"""
        if not context:
            return 0.0

        # Moyenne des pertinences
        avg_relevance = sum(result.relevance for result in context) / len(context)

        # Ajuster en fonction du nombre de résultats
        result_count_factor = min(len(context) / 5.0, 1.0)

        return avg_relevance * result_count_factor

    async def query(self, query: str, collection_name: str = 'champions',
                   filters: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """Méthode principale de requête RAG"""
        try:
            print(f"🎯 RAG: Requête complète pour '{query}'...")

            # 1. Recherche
            results = await self.search(query, collection_name, self.max_results, filters)

            if not results:
                return RAGResponse(
                    query=query,
                    answer="Aucun résultat trouvé pour cette requête.",
                    sources=[],
                    confidence=0.0,
                    context_used=[],
                    metadata={'status': 'no_results'}
                )

            # 2. Reranking
            reranked_results = await self.rerank_results(results, query)

            # 3. Génération de réponse
            response = await self.generate_response(query, reranked_results)

            return response

        except Exception as e:
            print(f"❌ RAG: Erreur lors de la requête: {e}")
            return RAGResponse(
                query=query,
                answer=f"Erreur lors du traitement de la requête: {str(e)}",
                sources=[],
                confidence=0.0,
                context_used=[],
                metadata={'error': str(e)}
            )

    async def search_champions(self, query: str, role: Optional[str] = None) -> RAGResponse:
        """Recherche des champions spécifiques"""
        filters = {}
        if role:
            filters['role'] = role

        return await self.query(query, 'champions', filters)

    async def search_matchups(self, query: str, role: Optional[str] = None) -> RAGResponse:
        """Recherche des matchups spécifiques"""
        filters = {}
        if role:
            filters['role'] = role

        return await self.query(query, 'matchups', filters)

    async def search_meta(self, query: str) -> RAGResponse:
        """Recherche dans les données de meta"""
        return await self.query(query, 'meta')

    async def search_players(self, query: str) -> RAGResponse:
        """Recherche des profils de joueurs"""
        return await self.query(query, 'players')

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de toutes les collections"""
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
            print(f"❌ RAG: Erreur lors de la récupération des stats: {e}")
            return {}

    async def hybrid_search(self, query: str, collection_name: str = 'champions',
                          alpha: float = 0.7) -> RAGResponse:
        """Recherche hybride combinant vectoriel et lexical"""
        try:
            print(f"🔍 RAG: Recherche hybride pour '{query}' (alpha={alpha})...")

            # Recherche vectorielle
            vector_results = await self.search(query, collection_name, limit=self.max_results)

            # Recherche lexicale (filtrage par nom)
            lexical_results = []
            for result in vector_results:
                data = result.payload.get('data', {})
                if 'name' in data:
                    name = data['name'].lower()
                    query_lower = query.lower()
                    if query_lower in name:
                        lexical_results.append(result)

            # Combiner les résultats
            combined_results = []

            # Ajouter les résultats vectoriels avec pondération alpha
            for result in vector_results:
                result.relevance = result.score * alpha
                combined_results.append(result)

            # Ajouter les résultats lexicaux avec pondération (1-alpha)
            for result in lexical_results:
                result.relevance = result.score * (1 - alpha) + 0.3  # Bonus pour match lexical
                combined_results.append(result)

            # Éliminer les doublons
            seen_ids = set()
            unique_results = []
            for result in combined_results:
                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    unique_results.append(result)

            # Trier par pertinence
            unique_results.sort(key=lambda x: x.relevance, reverse=True)

            # Générer la réponse
            response = await self.generate_response(query, unique_results[:self.top_k_results])

            return response

        except Exception as e:
            print(f"❌ RAG: Erreur lors de la recherche hybride: {e}")
            return RAGResponse(
                query=query,
                answer=f"Erreur lors de la recherche hybride: {str(e)}",
                sources=[],
                confidence=0.0,
                context_used=[],
                metadata={'error': str(e)}
            )

    def enable_reranking(self, enabled: bool = True) -> None:
        """Active ou désactive le reranking"""
        self.reranking_enabled = enabled
        print(f"🔄 RAG: Reranking {'activé' if enabled else 'désactivé'}")

    def set_max_results(self, max_results: int) -> None:
        """Définit le nombre maximum de résultats"""
        self.max_results = max_results
        print(f"📊 RAG: Maximum de résultats défini à {max_results}")

    def set_top_k_results(self, top_k: int) -> None:
        """Définit le nombre de résultats à retourner après reranking"""
        self.top_k_results = top_k
        print(f"🎯 RAG: Top-K résultats défini à {top_k}")

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent"""
        return {
            'name': self.agent_name,
            'role': self.agent_role,
            'capabilities': self.agent_capabilities,
            'status': 'active',
            'reranking_enabled': self.reranking_enabled,
            'max_results': self.max_results,
            'top_k_results': self.top_k_results,
            'collections': list(self.collections.values()),
            'vector_size': self.vector_size
        }