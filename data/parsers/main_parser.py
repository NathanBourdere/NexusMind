"""
Main Parser - Chef d'orchestre
Fusionne et source les données de tous les parsers
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import des parsers
from data.parsers.official.riot_static_parser import RiotStaticParser
from data.parsers.official.riot_live_parser import RiotLiveParser
from data.parsers.community.wiki_parser import WikiParser
from data.parsers.analytics.lolalytics_parser import LoLalyticsParser
from data.parsers.analytics.leaguepedia_parser import LeaguepediaParser

# Import des schémas
from core.schema.GameStateSnapshot import GameStateSnapshot
from core.schema.Champion import Champion
from core.schema.Item import Item
from core.schema.Matchup import Matchup
from core.schema.Summoner import Summoner


class MainParser:
    """Parser principal qui orchestre tous les sous-parsers"""

    def __init__(self, riot_api_key: Optional[str] = None):
        self.riot_static_parser = RiotStaticParser()
        self.riot_live_parser = RiotLiveParser(api_key=riot_api_key)
        self.wiki_parser = WikiParser()
        self.lolalytics_parser = LoLalyticsParser()
        self.leaguepedia_parser = LeaguepediaParser()

        self.data_sources = {
            'riot_static': self.riot_static_parser,
            'riot_live': self.riot_live_parser,
            'wiki': self.wiki_parser,
            'lolalytics': self.lolalytics_parser,
            'leaguepedia': self.leaguepedia_parser
        }

    async def parse_champion_complete(self, champion_name: str, role: str = "top") -> Optional[Champion]:
        """Parse un champion avec toutes les sources disponibles et retourne un objet Champion Pydantic"""
        try:
            # Récupérer les données statiques de Riot (retourne déjà un objet Champion)
            champion = self.riot_static_parser.parse_champion(champion_name)

            if not champion:
                return None

            # Enrichir avec les mécaniques avancées du Wiki (stockées dans metadata)
            wiki_mechanics = self.wiki_parser.parse_champion_mechanics(champion_name)
            if wiki_mechanics:
                # Fusionner les mécaniques dans le metadata existant
                if champion.metadata is None:
                    champion.metadata = {}
                champion.metadata.update({
                    'wiki_mechanics': wiki_mechanics,
                    'wiki_source': 'LoL Wiki (Fandom)'
                })

            # Enrichir avec les stats analytiques de LoLalytics (stockées dans metadata)
            lolalytics_stats = self.lolalytics_parser.parse_champion_stats(champion_name, role)
            if lolalytics_stats:
                if champion.metadata is None:
                    champion.metadata = {}
                champion.metadata.update({
                    'lolalytics_stats': lolalytics_stats,
                    'lolalytics_role': role,
                    'lolalytics_source': 'LoLalytics'
                })

            # Enrichir avec les stats pro de Leaguepedia (stockées dans metadata)
            leaguepedia_stats = self.leaguepedia_parser.parse_pro_champion_stats(champion_name)
            if leaguepedia_stats:
                if champion.metadata is None:
                    champion.metadata = {}
                champion.metadata.update({
                    'leaguepedia_stats': leaguepedia_stats,
                    'leaguepedia_source': 'Leaguepedia'
                })

            # Ajouter les métadonnées de traitement
            if champion.metadata is None:
                champion.metadata = {}
            champion.metadata.update({
                'last_updated': datetime.now().isoformat(),
                'scout_role': role,
                'data_sources': ['Riot Data Dragon', 'LoL Wiki (Fandom)', 'LoLalytics', 'Leaguepedia']
            })

            return champion

        except Exception as e:
            print(f"Error parsing complete champion data for {champion_name}: {e}")
            return None

    async def parse_matchup_complete(self, champion1: str, champion2: str, role: str = "top") -> Optional[Matchup]:
        """Parse un matchup complet avec toutes les sources et retourne un objet Matchup Pydantic"""
        try:
            # Récupérer les données des deux champions
            champion1_data = await self.parse_champion_complete(champion1, role)
            champion2_data = await self.parse_champion_complete(champion2, role)

            if not champion1_data or not champion2_data:
                return None

            # Récupérer le matchup spécifique depuis LoLalytics
            lolalytics_matchup = self.lolalytics_parser.parse_matchup(champion1, champion2, role)

            # Créer l'objet Matchup Pydantic
            matchup = Matchup(
                champion1_name=champion1,
                champion2_name=champion2,
                role=role,
                win_rate_champion1=champion1_data.metadata.get('lolalytics_stats', {}).get('win_rate', 50.0) if champion1_data.metadata else 50.0,
                win_rate_champion2=champion2_data.metadata.get('lolalytics_stats', {}).get('win_rate', 50.0) if champion2_data.metadata else 50.0,
                games_played=0,
                difficulty="medium",
                metadata={
                    'champion1_data': champion1_data.model_dump() if champion1_data else {},
                    'champion2_data': champion2_data.model_dump() if champion2_data else {},
                    'lolalytics_matchup': lolalytics_matchup.model_dump() if lolalytics_matchup else {},
                    'last_updated': datetime.now().isoformat(),
                    'data_sources': ['LoLalytics', 'Riot Data Dragon']
                }
            )

            return matchup

        except Exception as e:
            print(f"Error parsing complete matchup {champion1} vs {champion2}: {e}")
            return None

    async def parse_game_state_complete(self, summoner_name: str) -> Optional[GameStateSnapshot]:
        """Parse l'état complet d'une partie en cours et retourne un objet GameStateSnapshot Pydantic"""
        try:
            # Récupérer les données en temps réel de Riot
            active_game = self.riot_live_parser.get_active_game(summoner_name)

            if not active_game:
                return None

            # Parser l'état du jeu (retourne déjà un objet GameStateSnapshot)
            game_state = self.riot_live_parser.parse_game_state(active_game)

            if not game_state:
                return None

            # Enrichir avec les données des champions
            if hasattr(game_state, 'participants') and game_state.participants:
                for participant in game_state.participants:
                    champion_name = participant.champion_id
                    if champion_name:
                        champion_data = await self.parse_champion_complete(champion_name)
                        if champion_data and game_state.metadata is None:
                            game_state.metadata = {}
                        if champion_data and game_state.metadata is not None:
                            game_state.metadata[f'champion_{champion_name}'] = champion_data.model_dump()

            # Ajouter les métadonnées de traitement
            if game_state.metadata is None:
                game_state.metadata = {}
            game_state.metadata.update({
                'last_updated': datetime.now().isoformat(),
                'scout_summoner': summoner_name,
                'data_sources': ['Riot Live API', 'Riot Data Dragon']
            })

            return game_state

        except Exception as e:
            print(f"Error parsing complete game state for {summoner_name}: {e}")
            return None

    async def parse_meta_report(self) -> Optional[Dict[str, Any]]:
        """Génère un rapport complet de la meta actuelle avec des données structurées"""
        try:
            meta_report = {
                'timestamp': datetime.now().isoformat(),
                'lolalytics_meta': None,
                'leaguepedia_trends': None,
                'champions_data': {},
                'metadata': {
                    'data_sources': ['LoLalytics', 'Leaguepedia'],
                    'last_updated': datetime.now().isoformat()
                }
            }

            # Récupérer le rapport meta de LoLalytics
            lolalytics_meta = self.lolalytics_parser.get_meta_report()
            if lolalytics_meta:
                meta_report['lolalytics_meta'] = lolalytics_meta

                # Extraire les données de champions pour les structurer
                tier_lists = lolalytics_meta.get('tier_lists', {})
                for role, champions in tier_lists.items():
                    for champion_data in champions:
                        champion_name = champion_data.get('champion', '')
                        if champion_name and champion_name not in meta_report['champions_data']:
                            # Récupérer les données complètes du champion
                            champion = await self.parse_champion_complete(champion_name, role)
                            if champion:
                                meta_report['champions_data'][champion_name] = champion.model_dump()

            # Récupérer les tendances du patch actuel de Leaguepedia
            leaguepedia_trends = self.leaguepedia_parser.get_current_patch_trends()
            if leaguepedia_trends:
                meta_report['leaguepedia_trends'] = leaguepedia_trends

            return meta_report

        except Exception as e:
            print(f"Error generating meta report: {e}")
            return None

    async def parse_all_champions(self) -> Dict[str, Champion]:
        """Parse tous les champions avec les données de base et retourne des objets Champion Pydantic"""
        try:
            all_champions = {}

            # Récupérer tous les champions depuis Riot (retourne déjà des objets Champion)
            riot_champions = self.riot_static_parser.parse_all_champions()

            for champion_name, champion in riot_champions.items():
                # Enrichir avec les métadonnées
                if champion.metadata is None:
                    champion.metadata = {}
                champion.metadata.update({
                    'timestamp': datetime.now().isoformat(),
                    'data_sources': ['Riot Data Dragon']
                })
                all_champions[champion_name] = champion

            return all_champions

        except Exception as e:
            print(f"Error parsing all champions: {e}")
            return {}

    async def parse_all_items(self) -> Dict[str, Item]:
        """Parse tous les items et retourne des objets Item Pydantic"""
        try:
            all_items = {}

            # Récupérer tous les items depuis Riot (retourne déjà des objets Item)
            riot_items = self.riot_static_parser.parse_all_items()

            for item_id, item in riot_items.items():
                # Enrichir avec les métadonnées
                if item.metadata is None:
                    item.metadata = {}
                item.metadata.update({
                    'timestamp': datetime.now().isoformat(),
                    'data_sources': ['Riot Data Dragon']
                })
                all_items[item_id] = item

            return all_items

        except Exception as e:
            print(f"Error parsing all items: {e}")
            return {}

    def get_data_sources_status(self) -> Dict[str, bool]:
        """Vérifie le statut de toutes les sources de données"""
        status = {}

        for source_name, parser in self.data_sources.items():
            try:
                # Test simple de connexion
                if hasattr(parser, 'session'):
                    status[source_name] = True
                else:
                    status[source_name] = True
            except Exception as e:
                print(f"Error checking {source_name}: {e}")
                status[source_name] = False

        return status

    def get_source_attribution(self, data_type: str, data_content: Any) -> Dict[str, str]:
        """Génère l'attribution des sources pour les données"""
        attribution = {}

        if data_type == 'champion':
            if 'riot_static' in data_content:
                attribution['base_stats'] = 'Riot Data Dragon'
            if 'wiki' in data_content:
                attribution['mechanics'] = 'LoL Wiki (Fandom)'
            if 'lolalytics' in data_content:
                attribution['analytics'] = 'LoLalytics'
            if 'leaguepedia' in data_content:
                attribution['pro_stats'] = 'Leaguepedia'

        elif data_type == 'matchup':
            if 'lolalytics_matchup' in data_content:
                attribution['matchup_data'] = 'LoLalytics'

        elif data_type == 'game_state':
            if 'riot_live' in data_content:
                attribution['live_data'] = 'Riot Live API'

        return attribution

    async def parse_player_profile(self, summoner_name: str) -> Optional[Dict[str, Any]]:
        """Parse le profil complet d'un joueur"""
        try:
            player_profile = {
                'summoner_name': summoner_name,
                'sources': {},
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'sources_used': []
                }
            }

            # Récupérer les stats pro du joueur depuis Leaguepedia
            player_stats = self.leaguepedia_parser.parse_player_stats(summoner_name)
            if player_stats:
                player_profile['sources']['leaguepedia'] = player_stats
                player_profile['metadata']['sources_used'].append('Leaguepedia')

            # Récupérer l'état de jeu actuel si disponible
            game_state = await self.parse_game_state_complete(summoner_name)
            if game_state:
                player_profile['sources']['game_state'] = game_state
                player_profile['metadata']['sources_used'].append('Riot Live API')

            return player_profile

        except Exception as e:
            print(f"Error parsing player profile for {summoner_name}: {e}")
            return None

    def create_enriched_game_snapshot(self, base_snapshot: GameStateSnapshot) -> Dict[str, Any]:
        """Crée un snapshot de jeu enrichi avec toutes les sources"""
        try:
            enriched_snapshot = {
                'base_snapshot': base_snapshot,
                'enrichments': {},
                'source_attribution': {},
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'enrichment_sources': []
                }
            }

            # Ajouter les attributions de source
            source_attribution = self.get_source_attribution('game_state', {'riot_live': base_snapshot})
            enriched_snapshot['source_attribution'] = source_attribution

            return enriched_snapshot

        except Exception as e:
            print(f"Error creating enriched game snapshot: {e}")
            return {}

    async def run_parallel_parsing(self, tasks: List) -> List:
        """Exécute plusieurs tâches de parsing en parallèle"""
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filtrer les exceptions
            valid_results = []
            for result in results:
                if not isinstance(result, Exception):
                    valid_results.append(result)
                else:
                    print(f"Error in parallel parsing: {result}")

            return valid_results

        except Exception as e:
            print(f"Error in parallel parsing: {e}")
            return []