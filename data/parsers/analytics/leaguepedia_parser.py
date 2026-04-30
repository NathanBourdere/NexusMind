"""
Leaguepedia Parser - Pro Meta Data
Récupère les données de la scène compétitive depuis Leaguepedia
"""

import requests
import time
from typing import Dict, List, Any, Optional


class LeaguepediaParser:
    """Parser pour les données compétitives de Leaguepedia"""

    def __init__(self, rate_limit: float = 0.5):
        self.base_url = "https://lol.fandom.com"
        self.api_url = "https://lol.fandom.com/api.php"
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def __del__(self):
        """Ferme la session proprement"""
        if hasattr(self, 'session'):
            self.session.close()

    def _rate_limit_wait(self):
        """Applique le rate limiting entre les requêtes"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last_request)

        self.last_request_time = time.time()

    def _get_api_data(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Récupère les données depuis l'API Leaguepedia"""
        try:
            self._rate_limit_wait()

            default_params = {
                'action': 'query',
                'format': 'json',
                'origin': '*'
            }

            # Fusionner les params en donnant priorité aux params passés
            merged_params = {**default_params, **params}

            response = self.session.get(self.api_url, params=merged_params)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting API data: {e}")
            return None

    def _get_cargo_data(self, tables: str, fields: str, where: str = "", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Récupère les données depuis l'API Cargo de Leaguepedia"""
        try:
            self._rate_limit_wait()

            params = {
                'action': 'cargoquery',
                'tables': tables,
                'fields': fields,
                'where': where,
                'limit': str(limit),
                'format': 'json',
                'origin': '*'
            }

            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Extraire les résultats depuis la réponse Cargo
            if 'cargoquery' in data:
                return [item['title'] for item in data['cargoquery']]

            return []

        except Exception as e:
            print(f"Error getting Cargo data: {e}")
            return None

    def parse_tournament_data(self, tournament_name: str) -> Optional[Dict[str, Any]]:
        """Parse les données d'un tournoi spécifique"""
        try:
            # Utiliser l'API Cargo pour les données de tournoi
            tables = "Tournaments"
            fields = "Tournament,Year,Region,DateStart,DateEnd"
            where = f"Tournament LIKE '%{tournament_name}%'"

            cargo_data = self._get_cargo_data(tables, fields, where)

            if not cargo_data:
                return None

            tournament_data = {
                'source': 'Leaguepedia',
                'tournament': tournament_name,
                'teams': [],
                'matches': [],
                'champion_stats': {},
                'meta_trends': [],
                'details': cargo_data[0] if cargo_data else {}
            }

            return tournament_data

        except Exception as e:
            print(f"Error parsing tournament data for {tournament_name}: {e}")
            return None

    def parse_pro_champion_stats(self, champion_name: str, region: str = "LCK") -> Optional[Dict[str, Any]]:
        """Parse les stats pro d'un champion pour une région spécifique"""
        try:
            stats_data = {
                'source': 'Leaguepedia',
                'champion': champion_name,
                'region': region,
                'pick_rate': 0.0,
                'ban_rate': 0.0,
                'win_rate': 0.0,
                'games_played': 0,
                'teams': [],
                'players': [],
                'recent_performances': []
            }

            # Utiliser l'API Cargo pour les stats de champions
            tables = "MatchSchedule,ScoreboardGames"
            fields = "Tournament,Team1,Team2,Winner,Patch,DateTime"
            where = f"Team1 LIKE '%{champion_name}%' OR Team2 LIKE '%{champion_name}%'"

            cargo_data = self._get_cargo_data(tables, fields, where, limit=50)

            if cargo_data:
                stats_data['games_played'] = len(cargo_data)
                stats_data['recent_performances'] = cargo_data

                # Calculer le win rate basé sur les matchs
                wins = 0
                for match in cargo_data:
                    winner = match.get('Winner', '')
                    if champion_name.lower() in winner.lower():
                        wins += 1

                if stats_data['games_played'] > 0:
                    stats_data['win_rate'] = (wins / stats_data['games_played']) * 100

            return stats_data

        except Exception as e:
            print(f"Error parsing pro champion stats for {champion_name}: {e}")
            return None

    def parse_region_meta(self, region: str = "LCK") -> Optional[Dict[str, Any]]:
        """Parse la meta d'une région spécifique"""
        try:
            meta_data = {
                'source': 'Leaguepedia',
                'region': region,
                'top_champions': [],
                'rising_champions': [],
                'falling_champions': [],
                'team_compositions': [],
                'strategic_trends': []
            }

            # Utiliser l'API Cargo pour les données de la région
            tables = "Tournaments,ScoreboardGames"
            fields = "Tournament,Team1,Team2,Winner,Patch"
            where = f"Region='{region}'"

            cargo_data = self._get_cargo_data(tables, fields, where, limit=100)

            if cargo_data:
                # Extraire les champions joués depuis les matchs
                champions_played = {}
                for match in cargo_data:
                    team1 = match.get('Team1', '')
                    team2 = match.get('Team2', '')

                    # Note: En réalité, il faudrait parser les noms de champions
                    # depuis les données de match, mais c'est une simplification
                    if team1:
                        champions_played[team1] = champions_played.get(team1, 0) + 1
                    if team2:
                        champions_played[team2] = champions_played.get(team2, 0) + 1

                # Trier par nombre de matchs
                sorted_champions = sorted(champions_played.items(), key=lambda x: x[1], reverse=True)
                meta_data['top_champions'] = [champ[0] for champ in sorted_champions[:10]]

            return meta_data

        except Exception as e:
            print(f"Error parsing region meta for {region}: {e}")
            return None

    def parse_player_stats(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Parse les stats d'un joueur pro"""
        try:
            stats_data = {
                'source': 'Leaguepedia',
                'player': player_name,
                'team': '',
                'role': '',
                'champions': [],
                'kda': 0.0,
                'win_rate': 0.0,
                'games_played': 0,
                'signature_champions': []
            }

            # Utiliser l'API Cargo pour les stats de joueurs
            tables = "PlayerChampions,Players"
            fields = "Player,Team,Champion,K,D,A,WinRate,Games"
            where = f"Player LIKE '%{player_name}%'"

            cargo_data = self._get_cargo_data(tables, fields, where, limit=50)

            if cargo_data:
                stats_data['games_played'] = len(cargo_data)

                # Calculer les moyennes
                total_kda = 0
                total_win_rate = 0
                champions = []

                for player_data in cargo_data:
                    team = player_data.get('Team', '')
                    champion = player_data.get('Champion', '')

                    if team and not stats_data['team']:
                        stats_data['team'] = team

                    if champion:
                        champions.append(champion)

                    try:
                        k = float(player_data.get('K', 0))
                        d = float(player_data.get('D', 0))
                        a = float(player_data.get('A', 0))

                        if d > 0:
                            kda = (k + a) / d
                        else:
                            kda = k + a

                        total_kda += kda

                        win_rate = float(player_data.get('WinRate', 0))
                        total_win_rate += win_rate

                    except (ValueError, TypeError):
                        continue

                if stats_data['games_played'] > 0:
                    stats_data['kda'] = total_kda / stats_data['games_played']
                    stats_data['win_rate'] = total_win_rate / stats_data['games_played']

                stats_data['champions'] = champions
                stats_data['signature_champions'] = champions[:5]  # Top 5 champions

            return stats_data

        except Exception as e:
            print(f"Error parsing player stats for {player_name}: {e}")
            return None

    def get_competitive_regions(self) -> List[str]:
        """Retourne la liste des régions compétitives"""
        return [
            "LCK", "LPL", "LEC", "LCS",
            "LJL", "PCS", "VCS", "CBLOL",
            "LLA", "TCL", "LCL", "OPL"
        ]

    def get_current_patch_trends(self) -> Optional[Dict[str, Any]]:
        """Récupère les tendances du patch actuel"""
        try:
            trends_data = {
                'source': 'Leaguepedia',
                'patch': '',
                'global_trends': {},
                'regional_differences': {},
                'pro_vs_soloq': {}
            }

            # Récupérer les tendances pour les principales régions
            for region in self.get_competitive_regions()[:4]:  # Top 4 regions
                region_meta = self.parse_region_meta(region)
                if region_meta:
                    trends_data['regional_differences'][region] = region_meta

            return trends_data

        except Exception as e:
            print(f"Error getting current patch trends: {e}")
            return None

    def search_tournament(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Recherche des tournois"""
        try:
            tables = "Tournaments"
            fields = "Tournament,Year,Region,DateStart,DateEnd"
            where = f"Tournament LIKE '%{query}%'"

            cargo_data = self._get_cargo_data(tables, fields, where, limit=20)

            return cargo_data

        except Exception as e:
            print(f"Error searching tournaments: {e}")
            return None

    def get_recent_matches(self, region: str = "LCK", limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Récupère les matchs récents pour une région"""
        try:
            tables = "MatchSchedule"
            fields = "Tournament,Team1,Team2,DateTime,BestOf"
            where = f"Region='{region}' AND DateTime >= NOW() - INTERVAL 7 DAY"

            cargo_data = self._get_cargo_data(tables, fields, where, limit=limit)

            return cargo_data

        except Exception as e:
            print(f"Error getting recent matches: {e}")
            return None

    def get_team_stats(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Récupère les stats d'une équipe"""
        stats_data = {
                'source': 'Leaguepedia',
                'team': team_name,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'recent_matches': []
            }
        try:

            tables = "ScoreboardGames"
            fields = "Tournament,Team1,Team2,Winner,Patch,DateTime"
            where = f"Team1='{team_name}' OR Team2='{team_name}'"

            cargo_data = self._get_cargo_data(tables, fields, where, limit=50)

            if cargo_data:
                stats_data['recent_matches'] = cargo_data

                wins = 0
                losses = 0

                for match in cargo_data:
                    winner = match.get('Winner', '')
                    if winner == team_name:
                        wins += 1
                    else:
                        losses += 1

                stats_data['wins'] = wins
                stats_data['losses'] = losses

                total_games = wins + losses
                if total_games > 0:
                    stats_data['win_rate'] = (wins / total_games) * 100
        except Exception as e:
            print(f"Error getting team stats: {e}")
            return None