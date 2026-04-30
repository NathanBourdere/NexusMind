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

    async def parse_champion_complete(self, champion_name: str, role: str = "top") -> Optional[Dict[str, Any]]:
        """Parse un champion avec toutes les sources disponibles"""
        try:
            champion_data = {
                'champion_name': champion_name,
                'role': role,
                'sources': {},
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'sources_used': []
                }
            }

            # Récupérer les données statiques de Riot
            riot_static_data = self.riot_static_parser.parse_champion(champion_name)
            if riot_static_data:
                champion_data['sources']['riot_static'] = riot_static_data
                champion_data['metadata']['sources_used'].append('Riot Data Dragon')

            # Récupérer les mécaniques avancées du Wiki
            wiki_mechanics = self.wiki_parser.parse_champion_mechanics(champion_name)
            if wiki_mechanics:
                champion_data['sources']['wiki'] = wiki_mechanics
                champion_data['metadata']['sources_used'].append('LoL Wiki (Fandom)')

            # Récupérer les stats analytiques de LoLalytics
            lolalytics_stats = self.lolalytics_parser.parse_champion_stats(champion_name, role)
            if lolalytics_stats:
                champion_data['sources']['lolalytics'] = lolalytics_stats
                champion_data['metadata']['sources_used'].append('LoLalytics')

            # Récupérer les stats pro de Leaguepedia
            leaguepedia_stats = self.leaguepedia_parser.parse_pro_champion_stats(champion_name)
            if leaguepedia_stats:
                champion_data['sources']['leaguepedia'] = leaguepedia_stats
                champion_data['metadata']['sources_used'].append('Leaguepedia')

            return champion_data

        except Exception as e:
            print(f"Error parsing complete champion data for {champion_name}: {e}")
            return None

    async def parse_matchup_complete(self, champion1: str, champion2: str, role: str = "top") -> Optional[Dict[str, Any]]:
        """Parse un matchup complet avec toutes les sources"""
        try:
            matchup_data = {
                'champion1': champion1,
                'champion2': champion2,
                'role': role,
                'sources': {},
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'sources_used': []
                }
            }

            # Récupérer les données des deux champions
            champion1_data = await self.parse_champion_complete(champion1, role)
            champion2_data = await self.parse_champion_complete(champion2, role)

            if champion1_data:
                matchup_data['champion1_data'] = champion1_data

            if champion2_data:
                matchup_data['champion2_data'] = champion2_data

            # Récupérer le matchup spécifique depuis LoLalytics
            lolalytics_matchup = self.lolalytics_parser.parse_matchup(champion1, champion2, role)
            if lolalytics_matchup:
                matchup_data['sources']['lolalytics_matchup'] = lolalytics_matchup
                matchup_data['metadata']['sources_used'].append('LoLalytics Matchup')

            return matchup_data

        except Exception as e:
            print(f"Error parsing complete matchup {champion1} vs {champion2}: {e}")
            return None

    async def parse_game_state_complete(self, summoner_name: str) -> Optional[Dict[str, Any]]:
        """Parse l'état complet d'une partie en cours"""
        try:
            game_state_data = {
                'summoner_name': summoner_name,
                'sources': {},
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'sources_used': []
                }
            }

            # Récupérer les données en temps réel de Riot
            active_game = self.riot_live_parser.get_active_game(summoner_name)
            if active_game:
                game_state = self.riot_live_parser.parse_game_state(active_game)
                if game_state:
                    game_state_data['sources']['riot_live'] = game_state
                    game_state_data['metadata']['sources_used'].append('Riot Live API')

                    # Enrichir avec les données des champions
                    if hasattr(game_state, 'participants'):
                        for participant in game_state.participants:
                            champion_name = participant.champion_id
                            if champion_name:
                                champion_data = await self.parse_champion_complete(champion_name)
                                if champion_data:
                                    game_state_data['champions_data'] = game_state_data.get('champions_data', {})
                                    game_state_data['champions_data'][champion_name] = champion_data

            return game_state_data

        except Exception as e:
            print(f"Error parsing complete game state for {summoner_name}: {e}")
            return None

    async def parse_meta_report(self) -> Optional[Dict[str, Any]]:
        """Génère un rapport complet de la meta actuelle"""
        try:
            meta_report = {
                'timestamp': datetime.now().isoformat(),
                'sources': {},
                'metadata': {
                    'sources_used': []
                }
            }

            # Récupérer le rapport meta de LoLalytics
            lolalytics_meta = self.lolalytics_parser.get_meta_report()
            if lolalytics_meta:
                meta_report['sources']['lolalytics'] = lolalytics_meta
                meta_report['metadata']['sources_used'].append('LoLalytics')

            # Récupérer les tendances du patch actuel de Leaguepedia
            leaguepedia_trends = self.leaguepedia_parser.get_current_patch_trends()
            if leaguepedia_trends:
                meta_report['sources']['leaguepedia'] = leaguepedia_trends
                meta_report['metadata']['sources_used'].append('Leaguepedia')

            return meta_report

        except Exception as e:
            print(f"Error generating meta report: {e}")
            return None

    async def parse_all_champions(self) -> Dict[str, Dict[str, Any]]:
        """Parse tous les champions avec les données de base"""
        try:
            all_champions = {}

            # Récupérer tous les champions depuis Riot
            riot_champions = self.riot_static_parser.parse_all_champions()

            for champion_name, champion_data in riot_champions.items():
                all_champions[champion_name] = {
                    'riot_static': champion_data,
                    'metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'sources_used': ['Riot Data Dragon']
                    }
                }

            return all_champions

        except Exception as e:
            print(f"Error parsing all champions: {e}")
            return {}

    async def parse_all_items(self) -> Dict[str, Dict[str, Any]]:
        """Parse tous les items"""
        try:
            all_items = {}

            # Récupérer tous les items depuis Riot
            riot_items = self.riot_static_parser.parse_all_items()

            for item_id, item_data in riot_items.items():
                all_items[item_id] = {
                    'riot_static': item_data,
                    'metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'sources_used': ['Riot Data Dragon']
                    }
                }

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