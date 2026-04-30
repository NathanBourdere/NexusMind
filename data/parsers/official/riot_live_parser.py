"""
Riot Live Parser - Spectator v5 & Live Client
Récupère les données en temps réel d'une partie en cours
"""

import requests
from typing import Dict, List, Any, Optional
from core.schema.GameStateSnapshot import GameStateSnapshot
from core.schema.Summoner import Summoner
from core.schema.Team import Team
from core.schema.GameEvent import GameEvent


class RiotLiveParser:
    """Parser pour les données en temps réel de Riot (Spectator v5)"""

    def __init__(self, region: str = "euw1", api_key: Optional[str] = None):
        self.region = region
        self.api_key = api_key
        self.base_url = f"https://{region}.api.riotgames.com/lol/spectator/v5"
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({
                'X-Riot-Token': api_key
            })

    def _get_json(self, endpoint: str) -> Dict[str, Any]:
        """Récupère les données JSON depuis l'API"""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_active_game(self, summoner_name: str) -> Optional[Dict[str, Any]]:
        """Récupère la partie active d'un invocateur"""
        try:
            # D'abord récupérer le summoner ID
            summoner_url = f"https://{self.region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
            response = self.session.get(summoner_url)
            response.raise_for_status()
            summoner_data = response.json()

            summoner_id = summoner_data['id']

            # Récupérer la partie active
            game_data = self._get_json(f"active-games/by-summoner/{summoner_id}")
            return game_data

        except Exception as e:
            print(f"Error getting active game for {summoner_name}: {e}")
            return None

    def parse_game_state(self, game_data: Dict[str, Any]) -> Optional[GameStateSnapshot]:
        """Parse l'état complet du jeu"""
        try:
            # Parse participants
            participants = []
            for participant in game_data['participants']:
                summoner = Summoner(
                    summoner_id=participant['summonerId'],
                    summoner_name=participant['summonerName'],
                    champion_id=participant['championId'],
                    team_id=participant['teamId'],
                    metadata={
                        'source': 'Riot Live API',
                        'profile_icon_id': participant.get('profileIconId', 0),
                        'spell1_id': participant.get('spell1Id', 0),
                        'spell2_id': participant.get('spell2Id', 0),
                        'is_bot': participant.get('bot', False)
                    }
                )
                participants.append(summoner)

            # Parse teams
            teams = {}
            for team_data in game_data.get('teams', []):
                team = Team(
                    team_id=team_data['teamId'],
                    participant_ids=[p['summonerId'] for p in game_data['participants'] if p['teamId'] == team_data['teamId']],
                    total_gold=0,  # Will be updated from participant data
                    tower_count=0,
                    inhibitor_count=0,
                    metadata={
                        'source': 'Riot Live API',
                        'win': team_data.get('win', 'False'),
                        'first_dragon': team_data.get('firstDragon', False),
                        'first_inhibitor': team_data.get('firstInhibitor', False),
                        'first_baron': team_data.get('firstBaron', False),
                        'first_rift_herald': team_data.get('firstRiftHerald', False),
                        'first_tower': team_data.get('firstTower', False),
                        'first_blood': team_data.get('firstBlood', False)
                    }
                )
                teams[team_data['teamId']] = team

            # Parse game metadata
            game_state = GameStateSnapshot(
                game_id=game_data['gameId'],
                game_mode=game_data['gameMode'],
                game_type=game_data['gameType'],
                game_queue_config_id=game_data['gameQueueConfigId'],
                map_id=game_data['mapId'],
                game_start_time=game_data['gameStartTime'],
                game_length=0,  # Will be calculated
                participants=participants,
                teams=list(teams.values()),
                banned_champions=game_data.get('bannedChampions', []),
                game_customization_options=game_data.get('gameCustomizationOptions', {}),
                metadata={
                    'source': 'Riot Live API',
                    'platform_id': game_data['platformId'],
                    'observer_key': game_data.get('observers', {}).get('encryptionKey', ''),
                    'game_name': game_data.get('gameName', ''),
                    'game_type_name': game_data.get('gameTypeConfig', {}).get('name', '')
                }
            )

            return game_state

        except Exception as e:
            print(f"Error parsing game state: {e}")
            return None

    def get_featured_games(self) -> Optional[List[Dict[str, Any]]]:
        """Récupère les parties en vedette"""
        try:
            data = self._get_json("featured-games")
            return data.get('gameList', [])

        except Exception as e:
            print(f"Error getting featured games: {e}")
            return None

    def parse_live_client_data(self, port: int = 2999) -> Optional[Dict[str, Any]]:
        """Parse les données du client LoL en local (Live Client API)"""
        try:
            url = f"https://localhost:{port}/liveclientdata/allgamedata"
            response = self.session.get(url, verify=False)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting live client data: {e}")
            return None

    def parse_live_client_active_player(self, port: int = 2999) -> Optional[Dict[str, Any]]:
        """Parse les données du joueur actif depuis le client LoL"""
        try:
            url = f"https://localhost:{port}/liveclientdata/activeplayer"
            response = self.session.get(url, verify=False)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting active player data: {e}")
            return None

    def parse_live_client_player_stats(self, port: int = 2999) -> Optional[Dict[str, Any]]:
        """Parse les stats du joueur actif depuis le client LoL"""
        try:
            url = f"https://localhost:{port}/liveclientdata/activeplayerstats"
            response = self.session.get(url, verify=False)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting player stats: {e}")
            return None

    def parse_live_client_events(self, port: int = 2999) -> Optional[List[Dict[str, Any]]]:
        """Parse les événements de jeu depuis le client LoL"""
        try:
            url = f"https://localhost:{port}/liveclientdata/eventdata"
            response = self.session.get(url, verify=False)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting game events: {e}")
            return None

    def parse_game_events(self, events_data: List[Dict[str, Any]]) -> List[GameEvent]:
        """Parse les événements de jeu"""
        game_events = []

        for event_data in events_data:
            try:
                event = GameEvent(
                    event_id=str(event_data.get('EventID', '')),
                    event_type=event_data.get('EventName', ''),
                    timestamp=event_data.get('EventTime', 0.0),
                    killer_id=event_data.get('KillerName', ''),
                    victim_id=event_data.get('VictimName', ''),
                    assisting_ids=event_data.get('AssistingParticipants', []),
                    position_x=event_data.get('Position', {}).get('x', None),
                    position_y=event_data.get('Position', {}).get('y', None),
                    metadata={
                        'source': 'Riot Live Client API',
                        'raw_data': event_data
                    }
                )
                game_events.append(event)

            except Exception as e:
                print(f"Error parsing event: {e}")
                continue

        return game_events

    def get_match_timeline(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Récupère la timeline d'un match"""
        try:
            url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting match timeline: {e}")
            return None

    def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'un match"""
        try:
            url = f"https://{self.region}.api.riotgames.com/lol/match/v5/matches/{match_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting match details: {e}")
            return None