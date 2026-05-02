"""
LoLalytics Parser - Analytics Data
Récupère les données analytiques de meta depuis LoLalytics
"""

import requests
from typing import Dict, List, Any, Optional
from core.schema.Matchup import Matchup


class LoLalyticsParser:
    """Parser pour les données analytiques de LoLalytics"""

    def __init__(self):
        self.base_url = "https://lolalytics.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _get_json(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Récupère les données JSON depuis l'API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting data from {endpoint}: {e}")
            return None

    def parse_champion_stats(self, champion_name: str, role: str = "top") -> Optional[Dict[str, Any]]:
        """Parse les stats d'un champion pour un rôle spécifique"""
        try:
            # LoLalytics utilise des endpoints spécifiques par rôle
            endpoint = f"lol/{champion_name}/{role}/build/"
            data = self._get_json(endpoint)

            if not data:
                return None

            stats_data = {
                'source': 'LoLalytics',
                'champion': champion_name,
                'role': role,
                'win_rate': 0.0,
                'pick_rate': 0.0,
                'ban_rate': 0.0,
                'tier': '',
                'power_spikes': [],
                'best_items': [],
                'best_runes': [],
                'skill_order': [],
                'counters': [],
                'synergies': []
            }

            # Extraire les stats principales
            if 'winRate' in data:
                stats_data['win_rate'] = float(data['winRate'])
            if 'pickRate' in data:
                stats_data['pick_rate'] = float(data['pickRate'])
            if 'banRate' in data:
                stats_data['ban_rate'] = float(data['banRate'])
            if 'tier' in data:
                stats_data['tier'] = data['tier']

            # Extraire les power spikes
            if 'powerSpikes' in data:
                stats_data['power_spikes'] = data['powerSpikes']

            # Extraire les meilleurs items
            if 'items' in data:
                stats_data['best_items'] = self._parse_items_data(data['items'])

            # Extraire les meilleures runes
            if 'runes' in data:
                stats_data['best_runes'] = self._parse_runes_data(data['runes'])

            # Extraire l'ordre des compétences
            if 'skillOrder' in data:
                stats_data['skill_order'] = data['skillOrder']

            # Extraire les counters
            if 'counters' in data:
                stats_data['counters'] = self._parse_matchup_data(data['counters'])

            # Extraire les synergies
            if 'synergies' in data:
                stats_data['synergies'] = self._parse_matchup_data(data['synergies'])

            return stats_data

        except Exception as e:
            print(f"Error parsing champion stats for {champion_name}: {e}")
            return None

    def _parse_items_data(self, items_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse les données d'items"""
        parsed_items = []
        for item in items_data:
            try:
                parsed_item = {
                    'item_id': item.get('id', ''),
                    'item_name': item.get('name', ''),
                    'win_rate': float(item.get('winRate', 0.0)),
                    'pick_rate': float(item.get('pickRate', 0.0)),
                    'position': item.get('position', 0)
                }
                parsed_items.append(parsed_item)
            except (ValueError, TypeError):
                continue
        return parsed_items

    def _parse_runes_data(self, runes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse les données de runes"""
        parsed_runes = []
        for rune in runes_data:
            try:
                parsed_rune = {
                    'rune_id': rune.get('id', ''),
                    'rune_name': rune.get('name', ''),
                    'win_rate': float(rune.get('winRate', 0.0)),
                    'pick_rate': float(rune.get('pickRate', 0.0)),
                    'tree': rune.get('tree', ''),
                    'slot': rune.get('slot', 0)
                }
                parsed_runes.append(parsed_rune)
            except (ValueError, TypeError):
                continue
        return parsed_runes

    def _parse_matchup_data(self, matchup_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse les données de matchup"""
        parsed_matchups = []
        for matchup in matchup_data:
            try:
                parsed_matchup = {
                    'champion': matchup.get('champion', ''),
                    'win_rate': float(matchup.get('winRate', 0.0)),
                    'games_played': int(matchup.get('games', 0)),
                    'difficulty': matchup.get('difficulty', 'medium')
                }
                parsed_matchups.append(parsed_matchup)
            except (ValueError, TypeError):
                continue
        return parsed_matchups

    def parse_tier_list(self, role: str = "top") -> Optional[List[Dict[str, Any]]]:
        """Parse la tier list pour un rôle spécifique"""
        try:
            endpoint = f"lol/tier/list/{role}/"
            data = self._get_json(endpoint)

            if not data:
                return None

            tier_list = []
            for champion_data in data.get('champions', []):
                try:
                    champion_tier = {
                        'rank': champion_data.get('rank', 0),
                        'champion': champion_data.get('champion', ''),
                        'win_rate': float(champion_data.get('winRate', 0.0)),
                        'pick_rate': float(champion_data.get('pickRate', 0.0)),
                        'ban_rate': float(champion_data.get('banRate', 0.0)),
                        'tier': champion_data.get('tier', ''),
                        'games_played': int(champion_data.get('games', 0))
                    }
                    tier_list.append(champion_tier)
                except (ValueError, TypeError):
                    continue

            return tier_list

        except Exception as e:
            print(f"Error parsing tier list for {role}: {e}")
            return None

    def parse_all_roles_tier_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """Parse les tier lists pour tous les rôles"""
        roles = ["top", "jungle", "mid", "adc", "support"]
        tier_lists = {}

        for role in roles:
            tier_list = self.parse_tier_list(role)
            if tier_list:
                tier_lists[role] = tier_list

        return tier_lists

    def parse_matchup(self, champion1: str, champion2: str, role: str = "top") -> Optional[Matchup]:
        """Parse un matchup spécifique entre deux champions"""
        try:
            # Récupérer les stats des deux champions
            stats1 = self.parse_champion_stats(champion1, role)
            stats2 = self.parse_champion_stats(champion2, role)

            if not stats1 or not stats2:
                return None

            # Créer le matchup
            matchup = Matchup(
                champion1_name=champion1,
                champion2_name=champion2,
                role=role,
                win_rate_champion1=stats1.get('win_rate', 0.0),
                win_rate_champion2=stats2.get('win_rate', 0.0),
                games_played=0,
                difficulty="medium",
                metadata={
                    'source': 'LoLalytics',
                    'champion1_stats': stats1,
                    'champion2_stats': stats2,
                    'analysis': self._analyze_matchup(stats1, stats2)
                }
            )

            return matchup

        except Exception as e:
            print(f"Error parsing matchup {champion1} vs {champion2}: {e}")
            return None

    def _analyze_matchup(self, stats1: Dict[str, Any], stats2: Dict[str, Any]) -> str:
        """Analyse un matchup et retourne une description"""
        try:
            win_rate_diff = stats1.get('win_rate', 0.0) - stats2.get('win_rate', 0.0)

            if win_rate_diff > 5:
                return f"{stats1['champion']} a un avantage significatif ({win_rate_diff:.1f}% win rate diff)"
            elif win_rate_diff < -5:
                return f"{stats2['champion']} a un avantage significatif ({abs(win_rate_diff):.1f}% win rate diff)"
            else:
                return "Matchup équilibré"

        except Exception as e:
            print(f"Error analyzing matchup: {e}")
            return "Analyse non disponible"

    def get_meta_report(self) -> Optional[Dict[str, Any]]:
        """Génère un rapport de la meta actuelle"""
        try:
            meta_report = {
                'source': 'LoLalytics',
                'timestamp': requests.get('https://lolalytics.com').headers.get('Date', ''),
                'tier_lists': {},
                'top_champions': {},
                'rising_champions': {},
                'falling_champions': {}
            }

            # Récupérer les tier lists pour tous les rôles
            meta_report['tier_lists'] = self.parse_all_roles_tier_list()

            # Extraire les top champions par rôle
            for role, tier_list in meta_report['tier_lists'].items():
                if tier_list:
                    meta_report['top_champions'][role] = tier_list[:5]  # Top 5

            return meta_report

        except Exception as e:
            print(f"Error generating meta report: {e}")
            return None

    def search_champion(self, query: str) -> Optional[str]:
        """Recherche un champion"""
        try:
            # Essayer de normaliser le nom du champion
            normalized_query = query.lower().replace(' ', '').replace("'", '')

            # Liste des champions connus (à compléter)
            known_champions = [
                "aatrox", "ahri", "akali", "alistar", "amumu", "anivia", "annie",
                "aphelios", "ashe", "azir", "bard", "blitzcrank", "brand", "braum",
                "caitlyn", "camille", "cassiopeia", "cho", "corki", "darius",
                "diana", "drmundo", "ekko", "elise", "evelynn", "ezreal", "fiddle",
                "fiora", "fizz", "galio", "gangplank", "garen", "gnar", "gragas",
                "graves", "hecarim", "heimer", "illaoi", "irelia", "ivern", "janna",
                "jarvan", "jax", "jayce", "jhin", "jinx", "kaisa", "kalista", "karma",
                "karthus", "kassadin", "katarina", "kayle", "kayn", "kennen", "khazix",
                "kindred", "kled", "kogmaw", "leblanc", "lee", "leona", "lissandra",
                "lucian", "lulu", "lux", "malphite", "malzahar", "maokai", "master",
                "morgana", "nami", "nasus", "nautilus", "neeko", "nidalee", "nocturne",
                "nunu", "olaf", "orianna", "ornn", "pantheon", "poppy", "pyke",
                "qiyana", "quinn", "rakan", "rammus", "reksai", "rell", "renekton",
                "rengar", "riven", "rumble", "ryze", "sejuani", "senna", "seraphine",
                "set", "shaco", "shen", "shyvana", "singed", "sion", "sivir", "skarner",
                "sona", "soraka", "swain", "sylas", "syndra", "tahm", "taliyah", "talon",
                "taric", "teemo", "thresh", "tristana", "trundle", "tryndamere", "twisted",
                "twitch", "udyr", "urgot", "varus", "vayne", "veigar", "velkoz", "vi",
                "viego", "viktor", "vladimir", "volibear", "warwick", "wukong", "xayah",
                "xerath", "xinzhao", "yasuo", "yone", "yorick", "yuumi", "zac", "zed",
                "ziggs", "zilean", "zoe", "zyra"
            ]

            for champion in known_champions:
                if normalized_query in champion:
                    return champion

            return None

        except Exception as e:
            print(f"Error searching champion {query}: {e}")
            return None

    def set_champion_list(self, champion_list: List[str]) -> None:
        """Définit la liste des champions (pour éviter les appels API répétés)"""
        self.champion_list = champion_list

    def get_champion_list(self) -> List[str]:
        """Retourne la liste des champions"""
        return self.champion_list if hasattr(self, 'champion_list') else []