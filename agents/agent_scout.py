"""
Agent Scout - Agent d'exploration et de collecte de données
Premier agent du système multi-agents NexusMind
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

# Import du parser principal
from data.parsers.main_parser import MainParser


class ScoutAgent:
    """Agent Scout - Responsable de la collecte et de l'exploration des données"""

    def __init__(self, riot_api_key: Optional[str] = None, qdrant_url: str = "http://localhost:6333"):
        self.parser = MainParser(riot_api_key=riot_api_key)
        self.agent_name = "Scout"
        self.agent_role = "Data Collection & RAG Specialist"
        self.agent_capabilities = [
            "Collecte de données de champions",
            "Analyse de matchups",
            "Surveillance de parties en direct",
            "Rapports de meta actuelle",
            "Profiling de joueurs",
            "Stockage RAG avec Qdrant",
            "Recherche vectorielle de données"
        ]

        # Initialisation Qdrant
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collections = {
            'champions': 'nexusmind_champions',
            'matchups': 'nexusmind_matchups',
            'meta': 'nexusmind_meta',
            'players': 'nexusmind_players',
            'game_states': 'nexusmind_game_states'
        }

        # Créer les collections si elles n'existent pas
        self._initialize_qdrant_collections()

    def get_agent_info(self) -> Dict[str, Any]:
        """Retourne les informations de l'agent"""
        return {
            'name': self.agent_name,
            'role': self.agent_role,
            'capabilities': self.agent_capabilities,
            'status': 'active',
            'last_activity': datetime.now().isoformat(),
            'rag_enabled': True,
            'qdrant_collections': list(self.collections.values())
        }

    def _initialize_qdrant_collections(self):
        """Initialise les collections Qdrant si elles n'existent pas"""
        try:
            for collection_name in self.collections.values():
                self._create_collection_if_not_exists(collection_name)
            print("✅ Scout: Collections Qdrant initialisées")
        except Exception as e:
            print(f"❌ Scout: Erreur lors de l'initialisation des collections Qdrant: {e}")

    def _create_collection_if_not_exists(self, collection_name: str, vector_size: int = 1536):
        """Crée une collection Qdrant si elle n'existe pas"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                print(f"📁 Scout: Collection '{collection_name}' créée")
        except Exception as e:
            print(f"❌ Scout: Erreur lors de la création de la collection '{collection_name}': {e}")

    def _store_in_qdrant(self, collection_name: str, points: List[PointStruct]):
        """Stocke des points dans Qdrant"""
        try:
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"✅ Scout: {len(points)} points stockés dans '{collection_name}'")
            return True
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage dans '{collection_name}': {e}")
            return False

    def _create_point(self, data: Dict[str, Any], vector: List[float], collection_type: str) -> PointStruct:
        """Crée un point Qdrant à partir des données"""
        point_id = abs(hash(json.dumps(data, sort_keys=True))) % (10 ** 9)

        return PointStruct(
            id=point_id,
            vector=vector,
            payload={
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'collection_type': collection_type,
                'source': 'scout_agent'
            }
        )

    def _search_qdrant(self, collection_name: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche dans Qdrant"""
        try:
            results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            return [
                {
                    'id': hit.id,
                    'score': hit.score,
                    'payload': hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            print(f"❌ Scout: Erreur lors de la recherche dans '{collection_name}': {e}")
            return []

    def _generate_simple_vector(self, text: str) -> List[float]:
        """Génère un vecteur simple basé sur le texte (placeholder)"""
        # Note: En production, utilisez un vrai embedding model
        # Ici on utilise une méthode simple basée sur le hash du texte
        import hashlib

        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()

        # Convertir le hash en vecteur de 1536 dimensions
        vector = []
        for i in range(0, len(hash_hex), 2):
            hex_pair = hash_hex[i:i+2]
            value = int(hex_pair, 16) / 255.0  # Normaliser entre 0 et 1
            vector.append(value)

        # Étendre ou tronquer pour atteindre 1536 dimensions
        while len(vector) < 1536:
            vector.extend(vector[:min(1536 - len(vector), len(vector))])

        return vector[:1536]

    def store_champion_data(self, champion_data: Dict[str, Any]) -> bool:
        """Stocke les données d'un champion dans Qdrant"""
        try:
            # Créer un texte représentatif pour le vecteur
            text_representation = json.dumps(champion_data, sort_keys=True)
            vector = self._generate_simple_vector(text_representation)

            point = self._create_point(champion_data, vector, 'champion')
            return self._store_in_qdrant(self.collections['champions'], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage des données champion: {e}")
            return False

    def store_matchup_data(self, matchup_data: Dict[str, Any]) -> bool:
        """Stocke les données d'un matchup dans Qdrant"""
        try:
            text_representation = json.dumps(matchup_data, sort_keys=True)
            vector = self._generate_simple_vector(text_representation)

            point = self._create_point(matchup_data, vector, 'matchup')
            return self._store_in_qdrant(self.collections['matchups'], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage des données matchup: {e}")
            return False

    def store_meta_data(self, meta_data: Dict[str, Any]) -> bool:
        """Stocke les données de meta dans Qdrant"""
        try:
            text_representation = json.dumps(meta_data, sort_keys=True)
            vector = self._generate_simple_vector(text_representation)

            point = self._create_point(meta_data, vector, 'meta')
            return self._store_in_qdrant(self.collections['meta'], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage des données meta: {e}")
            return False

    def store_player_data(self, player_data: Dict[str, Any]) -> bool:
        """Stocke les données d'un joueur dans Qdrant"""
        try:
            text_representation = json.dumps(player_data, sort_keys=True)
            vector = self._generate_simple_vector(text_representation)

            point = self._create_point(player_data, vector, 'player')
            return self._store_in_qdrant(self.collections['players'], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage des données joueur: {e}")
            return False

    def store_game_state_data(self, game_state_data: Dict[str, Any]) -> bool:
        """Stocke les données d'état de jeu dans Qdrant"""
        try:
            text_representation = json.dumps(game_state_data, sort_keys=True)
            vector = self._generate_simple_vector(text_representation)

            point = self._create_point(game_state_data, vector, 'game_state')
            return self._store_in_qdrant(self.collections['game_states'], [point])
        except Exception as e:
            print(f"❌ Scout: Erreur lors du stockage des données d'état de jeu: {e}")
            return False

    def search_champions(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche des champions similaires"""
        query_vector = self._generate_simple_vector(query)
        return self._search_qdrant(self.collections['champions'], query_vector, limit)

    def search_matchups(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recherche des matchups similaires"""
        query_vector = self._generate_simple_vector(query)
        return self._search_qdrant(self.collections['matchups'], query_vector, limit)

    def get_collection_stats(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Retourne les statistiques d'une collection"""
        try:
            collection_info = self.qdrant_client.get_collection(collection_name)
            return {
                'name': collection_name,
                'points_count': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'status': collection_info.status
            }
        except Exception as e:
            print(f"❌ Scout: Erreur lors de la récupération des stats de '{collection_name}': {e}")
            return None

    def get_all_collections_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de toutes les collections"""
        stats = {}
        for collection_name in self.collections.values():
            collection_stats = self.get_collection_stats(collection_name)
            if collection_stats:
                stats[collection_name] = collection_stats
        return stats

    async def scout_champion(self, champion_name: str, role: str = "top", store_in_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Explore un champion spécifique et collecte toutes les données disponibles"""
        try:
            print(f"🔍 Scout: Exploration du champion {champion_name} (role: {role})...")

            # Collecter les données complètes du champion
            champion_data = await self.parser.parse_champion_complete(champion_name, role)

            if not champion_data:
                return None

            # Analyser les données collectées
            analysis = self._analyze_champion_data(champion_data)

            # Générer un rapport
            report = {
                'agent': self.agent_name,
                'action': 'champion_scout',
                'target': champion_name,
                'role': role,
                'timestamp': datetime.now().isoformat(),
                'data': champion_data,
                'analysis': analysis,
                'recommendations': self._generate_champion_recommendations(champion_data, analysis)
            }

            # Stocker dans Qdrant si demandé
            if store_in_rag:
                print(f"💾 Scout: Stockage des données de {champion_name} dans Qdrant...")
                self.store_champion_data(report)

            print(f"✅ Scout: Exploration de {champion_name} terminée")
            return report

        except Exception as e:
            print(f"❌ Scout: Erreur lors de l'exploration de {champion_name}: {e}")
            return None

    async def scout_matchup(self, champion1: str, champion2: str, role: str = "top", store_in_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Explore un matchup entre deux champions"""
        try:
            print(f"⚔️ Scout: Analyse du matchup {champion1} vs {champion2} (role: {role})...")

            # Collecter les données du matchup
            matchup_data = await self.parser.parse_matchup_complete(champion1, champion2, role)

            if not matchup_data:
                return None

            # Analyser le matchup
            analysis = self._analyze_matchup_data(matchup_data)

            # Générer un rapport
            report = {
                'agent': self.agent_name,
                'action': 'matchup_scout',
                'matchup': f"{champion1} vs {champion2}",
                'role': role,
                'timestamp': datetime.now().isoformat(),
                'data': matchup_data,
                'analysis': analysis,
                'recommendations': self._generate_matchup_recommendations(matchup_data, analysis)
            }

            # Stocker dans Qdrant si demandé
            if store_in_rag:
                print(f"💾 Scout: Stockage du matchup {champion1} vs {champion2} dans Qdrant...")
                self.store_matchup_data(report)

            print(f"✅ Scout: Analyse du matchup {champion1} vs {champion2} terminée")
            return report

        except Exception as e:
            print(f"❌ Scout: Erreur lors de l'analyse du matchup: {e}")
            return None

    async def scout_live_game(self, summoner_name: str, store_in_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Surveille une partie en cours"""
        try:
            print(f"🎮 Scout: Surveillance de la partie de {summoner_name}...")

            # Collecter l'état du jeu
            game_state = await self.parser.parse_game_state_complete(summoner_name)

            if not game_state:
                return None

            # Analyser l'état du jeu
            analysis = self._analyze_game_state(game_state)

            # Générer un rapport
            report = {
                'agent': self.agent_name,
                'action': 'live_game_scout',
                'target': summoner_name,
                'timestamp': datetime.now().isoformat(),
                'data': game_state,
                'analysis': analysis,
                'recommendations': self._generate_game_recommendations(game_state, analysis)
            }

            # Stocker dans Qdrant si demandé
            if store_in_rag:
                print(f"💾 Scout: Stockage de l'état de jeu de {summoner_name} dans Qdrant...")
                self.store_game_state_data(report)

            print(f"✅ Scout: Surveillance de la partie de {summoner_name} terminée")
            return report

        except Exception as e:
            print(f"❌ Scout: Erreur lors de la surveillance de la partie: {e}")
            return None

    async def scout_meta_report(self, store_in_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Génère un rapport complet de la meta actuelle"""
        try:
            print("📊 Scout: Génération du rapport meta...")

            # Collecter les données de meta
            meta_data = await self.parser.parse_meta_report()

            if not meta_data:
                return None

            # Analyser la meta
            analysis = self._analyze_meta_data(meta_data)

            # Générer un rapport
            report = {
                'agent': self.agent_name,
                'action': 'meta_report',
                'timestamp': datetime.now().isoformat(),
                'data': meta_data,
                'analysis': analysis,
                'recommendations': self._generate_meta_recommendations(meta_data, analysis)
            }

            # Stocker dans Qdrant si demandé
            if store_in_rag:
                print("💾 Scout: Stockage du rapport meta dans Qdrant...")
                self.store_meta_data(report)

            print("✅ Scout: Rapport meta généré")
            return report

        except Exception as e:
            print(f"❌ Scout: Erreur lors de la génération du rapport meta: {e}")
            return None

    async def scout_player_profile(self, summoner_name: str, store_in_rag: bool = True) -> Optional[Dict[str, Any]]:
        """Explore le profil d'un joueur"""
        try:
            print(f"👤 Scout: Exploration du profil de {summoner_name}...")

            # Collecter les données du joueur
            player_data = await self.parser.parse_player_profile(summoner_name)

            if not player_data:
                return None

            # Analyser le profil
            analysis = self._analyze_player_data(player_data)

            # Générer un rapport
            report = {
                'agent': self.agent_name,
                'action': 'player_profile_scout',
                'target': summoner_name,
                'timestamp': datetime.now().isoformat(),
                'data': player_data,
                'analysis': analysis,
                'recommendations': self._generate_player_recommendations(player_data, analysis)
            }

            # Stocker dans Qdrant si demandé
            if store_in_rag:
                print(f"💾 Scout: Stockage du profil de {summoner_name} dans Qdrant...")
                self.store_player_data(report)

            print(f"✅ Scout: Profil de {summoner_name} exploré")
            return report

        except Exception as e:
            print(f"❌ Scout: Erreur lors de l'exploration du profil: {e}")
            return None

    def _analyze_champion_data(self, champion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les données d'un champion"""
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'power_spikes': [],
            'best_matchups': [],
            'worst_matchups': [],
            'meta_position': ''
        }

        # Extraire les informations des différentes sources
        sources = champion_data.get('sources', {})

        # Analyser les stats LoLalytics
        if 'lolalytics' in sources:
            lolalytics_data = sources['lolalytics']
            win_rate = lolalytics_data.get('win_rate', 0)
            pick_rate = lolalytics_data.get('pick_rate', 0)
            tier = lolalytics_data.get('tier', '')

            analysis['meta_position'] = f"Tier {tier} ({win_rate:.1f}% WR, {pick_rate:.1f}% PR)"

            if win_rate > 52:
                analysis['strengths'].append(f"Fort win rate ({win_rate:.1f}%)")
            elif win_rate < 48:
                analysis['weaknesses'].append(f"Win rate faible ({win_rate:.1f}%)")

            if pick_rate > 10:
                analysis['strengths'].append(f"Très populaire ({pick_rate:.1f}% pick rate)")
            elif pick_rate < 2:
                analysis['weaknesses'].append(f"Peu joué ({pick_rate:.1f}% pick rate)")

            # Extraire les power spikes
            power_spikes = lolalytics_data.get('power_spikes', [])
            if power_spikes:
                analysis['power_spikes'] = power_spikes

            # Extraire les matchups
            counters = lolalytics_data.get('counters', [])
            if counters:
                analysis['worst_matchups'] = [c['champion'] for c in counters[:3]]

            synergies = lolalytics_data.get('synergies', [])
            if synergies:
                analysis['best_matchups'] = [s['champion'] for s in synergies[:3]]

        # Analyser les mécaniques du Wiki
        if 'wiki' in sources:
            wiki_data = sources['wiki']
            hidden_mechanics = wiki_data.get('hidden_mechanics', [])
            if hidden_mechanics:
                analysis['strengths'].extend([f"Mécanique cachée: {m}" for m in hidden_mechanics[:2]])

        return analysis

    def _analyze_matchup_data(self, matchup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les données d'un matchup"""
        analysis = {
            'advantage': '',
            'difficulty': '',
            'key_factors': [],
            'win_probability': 0.0
        }

        # Analyser les données des deux champions
        champion1_data = matchup_data.get('champion1_data', {})
        champion2_data = matchup_data.get('champion2_data', {})

        # Extraire les win rates
        c1_wr = champion1_data.get('sources', {}).get('lolalytics', {}).get('win_rate', 50)
        c2_wr = champion2_data.get('sources', {}).get('lolalytics', {}).get('win_rate', 50)

        # Déterminer l'avantage
        wr_diff = c1_wr - c2_wr
        if abs(wr_diff) < 2:
            analysis['advantage'] = "Équilibré"
            analysis['difficulty'] = "Medium"
        elif wr_diff > 0:
            analysis['advantage'] = f"Avantage {matchup_data.get('champion1', 'Champion 1')}"
            analysis['difficulty'] = "Easy" if wr_diff > 5 else "Medium"
        else:
            analysis['advantage'] = f"Avantage {matchup_data.get('champion2', 'Champion 2')}"
            analysis['difficulty'] = "Easy" if abs(wr_diff) > 5 else "Medium"

        # Calculer la probabilité de victoire
        analysis['win_probability'] = 50 + (wr_diff / 2)

        # Identifier les facteurs clés
        if abs(wr_diff) > 3:
            analysis['key_factors'].append(f"Différence de win rate significative ({abs(wr_diff):.1f}%)")

        return analysis

    def _analyze_game_state(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse l'état d'une partie en cours"""
        analysis = {
            'game_phase': '',
            'winning_team': '',
            'key_objectives': [],
            'critical_moments': []
        }

        # Analyser les données de la partie
        sources = game_state.get('sources', {})

        if 'riot_live' in sources:
            live_data = sources['riot_live']

            # Déterminer la phase de jeu
            game_length = live_data.get('game_length', 0)
            if game_length < 15:
                analysis['game_phase'] = "Early Game"
            elif game_length < 30:
                analysis['game_phase'] = "Mid Game"
            else:
                analysis['game_phase'] = "Late Game"

            # Analyser les équipes
            teams = live_data.get('teams', [])
            if teams:
                # Trouver l'équipe qui gagne
                for team in teams:
                    total_gold = team.get('total_gold', 0)
                    tower_count = team.get('tower_count', 0)

                    if total_gold > 0 or tower_count > 0:
                        if not analysis['winning_team']:
                            analysis['winning_team'] = f"Team {team.get('team_id', 'Unknown')}"

        return analysis

    def _analyze_meta_data(self, meta_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les données de la meta"""
        analysis = {
            'meta_tier': '',
            'dominant_champions': [],
            'rising_champions': [],
            'falling_champions': [],
            'key_trends': []
        }

        # Analyser les données de LoLalytics
        if 'lolalytics' in meta_data.get('sources', {}):
            lolalytics_data = meta_data['sources']['lolalytics']
            tier_lists = lolalytics_data.get('tier_lists', {})

            # Extraire les champions dominants par rôle
            for role, champions in tier_lists.items():
                if champions:
                    top_champions = [c['champion'] for c in champions[:3]]
                    analysis['dominant_champions'].extend([f"{role}: {', '.join(top_champions)}"])

        # Analyser les tendances
        if 'leaguepedia' in meta_data.get('sources', {}):
            leaguepedia_data = meta_data['sources']['leaguepedia']
            regional_diffs = leaguepedia_data.get('regional_differences', {})

            for region, region_meta in regional_diffs.items():
                top_champs = region_meta.get('top_champions', [])
                if top_champs:
                    analysis['key_trends'].append(f"{region}: {', '.join(top_champs[:3])}")

        return analysis

    def _analyze_player_data(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les données d'un joueur"""
        analysis = {
            'skill_level': '',
            'main_champions': [],
            'playstyle': '',
            'strengths': [],
            'weaknesses': []
        }

        # Analyser les stats du joueur
        sources = player_data.get('sources', {})

        if 'leaguepedia' in sources:
            player_stats = sources['leaguepedia']
            win_rate = player_stats.get('win_rate', 0)
            kda = player_stats.get('kda', 0)

            # Déterminer le niveau de skill
            if win_rate > 60 and kda > 4:
                analysis['skill_level'] = "Elite"
            elif win_rate > 55 and kda > 3:
                analysis['skill_level'] = "High"
            elif win_rate > 50:
                analysis['skill_level'] = "Average"
            else:
                analysis['skill_level'] = "Below Average"

            # Analyser le style de jeu
            if kda > 4:
                analysis['playstyle'] = "Aggressive"
            elif kda > 2:
                analysis['playstyle'] = "Balanced"
            else:
                analysis['playstyle'] = "Defensive"

            # Extraire les champions principaux
            signature_champs = player_stats.get('signature_champions', [])
            if signature_champs:
                analysis['main_champions'] = signature_champs

        return analysis

    def _generate_champion_recommendations(self, champion_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour un champion"""
        recommendations = []

        if analysis.get('strengths'):
            recommendations.append(f"Capitaliser sur: {', '.join(analysis['strengths'])}")

        if analysis.get('weaknesses'):
            recommendations.append(f"Attention à: {', '.join(analysis['weaknesses'])}")

        if analysis.get('power_spikes'):
            recommendations.append(f"Power spikes: {', '.join([str(p) for p in analysis['power_spikes']])}")

        return recommendations

    def _generate_matchup_recommendations(self, matchup_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour un matchup"""
        recommendations = []

        advantage = analysis.get('advantage', '')
        if advantage and advantage != "Équilibré":
            recommendations.append(f"{advantage} - Jouer agressivement")
        else:
            recommendations.append("Matchup équilibré - Focus sur le farm et les erreurs adverses")

        difficulty = analysis.get('difficulty', '')
        if difficulty == "Easy":
            recommendations.append("Difficulté faible - Chercher à dominer la lane")
        elif difficulty == "Hard":
            recommendations.append("Difficulté élevée - Jouer prudemment et attendre le gank")

        return recommendations

    def _generate_game_recommendations(self, game_state: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour une partie en cours"""
        recommendations = []

        game_phase = analysis.get('game_phase', '')
        if game_phase == "Early Game":
            recommendations.append("Focus sur le farm et les objectifs de lane")
        elif game_phase == "Mid Game":
            recommendations.append("Rotations et objectifs d'équipe")
        elif game_phase == "Late Game":
            recommendations.append("Team fights et objectifs majeurs")

        return recommendations

    def _generate_meta_recommendations(self, meta_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur la meta"""
        recommendations = []

        if analysis.get('dominant_champions'):
            recommendations.append(f"Champions dominants: {', '.join(analysis['dominant_champions'][:3])}")

        if analysis.get('key_trends'):
            recommendations.append(f"Tendances clés: {', '.join(analysis['key_trends'][:2])}")

        return recommendations

    def _generate_player_recommendations(self, player_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour un joueur"""
        recommendations = []

        skill_level = analysis.get('skill_level', '')
        if skill_level == "Elite":
            recommendations.append("Niveau élite - Considérer le jeu compétitif")
        elif skill_level == "High":
            recommendations.append("Bon niveau - Continuer à améliorer les mécaniques")
        elif skill_level == "Average":
            recommendations.append("Niveau moyen - Travailler la cohérence")
        else:
            recommendations.append("Niveau en amélioration - Focus sur les fondamentaux")

        playstyle = analysis.get('playstyle', '')
        if playstyle:
            recommendations.append(f"Style de jeu: {playstyle}")

        return recommendations

    async def execute_mission(self, mission_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Exécute une mission spécifique"""
        missions = {
            'champion': self.scout_champion,
            'matchup': self.scout_matchup,
            'live_game': self.scout_live_game,
            'meta_report': self.scout_meta_report,
            'player_profile': self.scout_player_profile
        }

        mission_func = missions.get(mission_type)
        if mission_func:
            return await mission_func(**kwargs)
        else:
            print(f"❌ Scout: Mission inconnue - {mission_type}")
            return None

    async def populate_rag_with_all_data(self, champions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Peuple le RAG avec toutes les données disponibles"""
        try:
            print("🚀 Scout: Peuplement du RAG avec toutes les données...")

            results = {
                'timestamp': datetime.now().isoformat(),
                'champions_processed': 0,
                'matchups_processed': 0,
                'meta_reports': 0,
                'player_profiles': 0,
                'errors': []
            }

            # Si aucune liste de champions n'est fournie, utiliser une liste par défaut
            if not champions:
                champions = ["Aatrox", "Ahri", "Akali", "Yasuo", "Zed"]

            # Traiter chaque champion
            for champion in champions:
                try:
                    print(f"📊 Traitement de {champion}...")
                    await self.scout_champion(champion, store_in_rag=True)
                    results['champions_processed'] += 1
                except Exception as e:
                    error_msg = f"Erreur lors du traitement de {champion}: {e}"
                    print(f"❌ {error_msg}")
                    results['errors'].append(error_msg)

            # Générer et stocker un rapport meta
            try:
                print("📊 Génération du rapport meta...")
                await self.scout_meta_report(store_in_rag=True)
                results['meta_reports'] += 1
            except Exception as e:
                error_msg = f"Erreur lors de la génération du rapport meta: {e}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)

            # Afficher les statistiques finales
            print(f"✅ Scout: Peuplement du RAG terminé!")
            print(f"📊 Statistiques:")
            print(f"   - Champions traités: {results['champions_processed']}")
            print(f"   - Rapports meta: {results['meta_reports']}")
            print(f"   - Erreurs: {len(results['errors'])}")

            # Afficher les stats des collections Qdrant
            print(f"📊 Statistiques des collections Qdrant:")
            all_stats = self.get_all_collections_stats()
            for collection_name, stats in all_stats.items():
                print(f"   - {collection_name}: {stats['points_count']} points")

            return results

        except Exception as e:
            print(f"❌ Scout: Erreur lors du peuplement du RAG: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }

    def save_report(self, report: Dict[str, Any], filename: str) -> bool:
        """Sauvegarde un rapport dans un fichier JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📁 Scout: Rapport sauvegardé dans {filename}")
            return True
        except Exception as e:
            print(f"❌ Scout: Erreur lors de la sauvegarde du rapport: {e}")
            return False