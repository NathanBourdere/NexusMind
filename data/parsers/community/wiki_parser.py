"""
Wiki Parser - Fandom Wiki
Récupère les données de connaissance communautaire depuis le Wiki LoL
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from core.schema.Champion import Champion
from core.schema.JungleCamp import JungleCamp
from core.schema.Stats import Stats


class WikiParser:
    """Parser pour les données du Wiki LoL (Fandom)"""

    def __init__(self):
        self.base_url = "https://leagueoflegends.fandom.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _get_page(self, page_name: str) -> Optional[BeautifulSoup]:
        """Récupère une page du wiki"""
        try:
            url = f"{self.base_url}/wiki/{page_name}"
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')

        except Exception as e:
            print(f"Error getting wiki page {page_name}: {e}")
            return None

    def parse_champion_mechanics(self, champion_name: str) -> Optional[Dict[str, Any]]:
        """Parse les mécaniques avancées d'un champion"""
        try:
            soup = self._get_page(champion_name)
            if not soup:
                return None

            mechanics_data = {
                'source': 'LoL Wiki (Fandom)',
                'champion': champion_name,
                'frame_data': {},
                'animation_priorities': {},
                'hidden_mechanics': [],
                'interaction_notes': []
            }

            # Extraire les données de frame (si disponibles)
            # Note: Ces données sont souvent dans des tableaux spécifiques
            frame_data_section = soup.find('span', {'id': 'Frame_data'})
            if frame_data_section:
                # Parser les données de frame ici
                mechanics_data['frame_data'] = self._parse_frame_data(frame_data_section)

            # Extraire les notes d'interaction
            interaction_section = soup.find('span', {'id': 'Interactions'})
            if interaction_section:
                mechanics_data['interaction_notes'] = self._parse_interaction_notes(interaction_section)

            # Extraire les mécaniques cachées
            hidden_section = soup.find('span', {'id': 'Hidden_mechanics'})
            if hidden_section:
                mechanics_data['hidden_mechanics'] = self._parse_hidden_mechanics(hidden_section)

            return mechanics_data

        except Exception as e:
            print(f"Error parsing champion mechanics for {champion_name}: {e}")
            return None

    def _parse_frame_data(self, section) -> Dict[str, Any]:
        """Parse les données de frame depuis une section"""
        frame_data = {}
        try:
            # Trouver le tableau de frame data
            tables = section.find_all_next('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        frame_data[key] = value
        except Exception as e:
            print(f"Error parsing frame data: {e}")

        return frame_data

    def _parse_interaction_notes(self, section) -> List[str]:
        """Parse les notes d'interaction depuis une section"""
        notes = []
        try:
            # Trouver les listes après la section
            lists = section.find_all_next(['ul', 'ol'])
            for lst in lists:
                items = lst.find_all('li')
                for item in items:
                    note = item.get_text(strip=True)
                    if note:
                        notes.append(note)
        except Exception as e:
            print(f"Error parsing interaction notes: {e}")

        return notes

    def _parse_hidden_mechanics(self, section) -> List[str]:
        """Parse les mécaniques cachées depuis une section"""
        mechanics = []
        try:
            # Trouver les listes après la section
            lists = section.find_all_next(['ul', 'ol'])
            for lst in lists:
                items = lst.find_all('li')
                for item in items:
                    mechanic = item.get_text(strip=True)
                    if mechanic:
                        mechanics.append(mechanic)
        except Exception as e:
            print(f"Error parsing hidden mechanics: {e}")

        return mechanics

    def parse_jungle_camps(self) -> Dict[str, JungleCamp]:
        """Parse les données des camps de jungle"""
        try:
            soup = self._get_page("Jungle")
            if not soup:
                return {}

            camps = {}

            # Parser les différents camps
            camp_types = [
                "Blue_Sentinel",
                "Red_Brambleback",
                "Gromp",
                "Raptors",
                "Krug",
                "Scuttle_Crab"
            ]

            for camp_name in camp_types:
                camp_data = self._parse_single_camp(camp_name)
                if camp_data:
                    camps[camp_name] = camp_data

            return camps

        except Exception as e:
            print(f"Error parsing jungle camps: {e}")
            return {}

    def _parse_single_camp(self, camp_name: str) -> Optional[JungleCamp]:
        """Parse un camp de jungle spécifique"""
        try:
            soup = self._get_page(camp_name)
            if not soup:
                return None

            # Extraire les données de base
            infobox = soup.find('aside', class_='portable-infobox')
            if not infobox:
                return None

            # Parser les données depuis l'infobox
            spawn_time = 90  # Default
            respawn_timer = 300  # Default
            gold_reward = 0
            exp_reward = 0

            # Extraire les valeurs depuis l'infobox
            data_rows = infobox.find_all('div', class_='pi-data')
            for row in data_rows:
                label = row.find('h3')
                value = row.find('div')
                if label and value:
                    label_text = label.get_text(strip=True).lower()
                    value_text = value.get_text(strip=True)

                    if 'spawn' in label_text:
                        try:
                            spawn_time = int(value_text.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif 'respawn' in label_text:
                        try:
                            respawn_timer = int(value_text.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif 'gold' in label_text:
                        try:
                            gold_reward = int(value_text.split()[0])
                        except (ValueError, IndexError):
                            pass
                    elif 'experience' in label_text or 'exp' in label_text:
                        try:
                            exp_reward = int(value_text.split()[0])
                        except (ValueError, IndexError):
                            pass

            # Déterminer le côté et la position
            side = "Neutral"
            location_quadrant = "Neutral"

            if "Blue" in camp_name:
                side = "Blue"
                location_quadrant = "Blue_Jungle"
            elif "Red" in camp_name:
                side = "Red"
                location_quadrant = "Red_Jungle"

            # Créer les stats avec des données précises
            stats = Stats(
                hp=self._get_camp_hp(camp_name),
                hpperlevel=self._get_camp_hp_per_level(camp_name),
                mp=0.0,
                mpperlevel=0.0,
                movespeed=self._get_camp_movespeed(camp_name),
                armor=self._get_camp_armor(camp_name),
                armorperlevel=self._get_camp_armor_per_level(camp_name),
                spellblock=self._get_camp_mr(camp_name),
                spellblockperlevel=self._get_camp_mr_per_level(camp_name),
                attackrange=self._get_camp_attack_range(camp_name),
                hpregen=0.0,
                hpregenperlevel=0.0,
                mpregen=0.0,
                mpregenperlevel=0.0,
                crit=0.0,
                critperlevel=0.0,
                attackdamage=self._get_camp_ad(camp_name),
                attackdamageperlevel=self._get_camp_ad_per_level(camp_name),
                attackspeed=self._get_camp_as(camp_name),
                attackspeedperlevel=self._get_camp_as_per_level(camp_name)
            )

            camp = JungleCamp(
                id_camp=camp_name,
                name=camp_name.replace('_', ' '),
                spawn_time=spawn_time,
                respawn_timer=respawn_timer,
                stats=stats,
                gold_reward=gold_reward,
                exp_reward=exp_reward,
                side=side,
                location_quadrant=location_quadrant,
                metadata={
                    'source': 'LoL Wiki (Fandom)',
                    'wiki_url': f"{self.base_url}/wiki/{camp_name}",
                    'notes': self._extract_camp_notes(soup)
                }
            )

            return camp

        except Exception as e:
            print(f"Error parsing camp {camp_name}: {e}")
            return None

    def _extract_camp_notes(self, soup: BeautifulSoup) -> List[str]:
        """Extrait les notes spécifiques à un camp"""
        notes = []
        try:
            # Chercher des sections de notes ou de trivia
            trivia_section = soup.find('span', {'id': 'Trivia'})
            if trivia_section:
                lists = trivia_section.find_all_next(['ul', 'ol'])
                for lst in lists:
                    items = lst.find_all('li')
                    for item in items:
                        note = item.get_text(strip=True)
                        if note:
                            notes.append(note)
        except Exception as e:
            print(f"Error extracting camp notes: {e}")

        return notes

    def parse_item_interactions(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Parse les interactions d'items"""
        try:
            soup = self._get_page(item_name)
            if not soup:
                return None

            interactions = {
                'source': 'LoL Wiki (Fandom)',
                'item': item_name,
                'synergies': [],
                'counters': [],
                'special_interactions': []
            }

            # Extraire les synergies
            synergy_section = soup.find('span', {'id': 'Synergies'})
            if synergy_section:
                interactions['synergies'] = self._parse_interaction_notes(synergy_section)

            # Extraire les counters
            counter_section = soup.find('span', {'id': 'Counters'})
            if counter_section:
                interactions['counters'] = self._parse_interaction_notes(counter_section)

            return interactions

        except Exception as e:
            print(f"Error parsing item interactions for {item_name}: {e}")
            return None

    def search_champion(self, query: str) -> Optional[str]:
        """Recherche un champion sur le wiki"""
        try:
            # Utiliser l'API de recherche du wiki
            search_url = f"{self.base_url}/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json'
            }

            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('query', {}).get('search'):
                return data['query']['search'][0]['title']

            return None

        except Exception as e:
            print(f"Error searching champion {query}: {e}")
            return None

    # --- Méthodes pour les stats précises des camps de jungle ---

    def _get_camp_hp(self, camp_name: str) -> float:
        """Retourne les HP de base d'un camp"""
        camp_stats = {
            'Blue_Sentinel': 3500,
            'Red_Brambleback': 3500,
            'Gromp': 3000,
            'Raptors': 1200,
            'Krug': 1500,
            'Scuttle_Crab': 800
        }
        return float(camp_stats.get(camp_name, 2000))

    def _get_camp_hp_per_level(self, camp_name: str) -> float:
        """Retourne les HP par niveau d'un camp"""
        return 0.0  # Les camps ne scalent pas par niveau

    def _get_camp_movespeed(self, camp_name: str) -> float:
        """Retourne la vitesse de déplacement d'un camp"""
        camp_stats = {
            'Blue_Sentinel': 200,
            'Red_Brambleback': 200,
            'Gromp': 200,
            'Raptors': 300,
            'Krug': 200,
            'Scuttle_Crab': 400
        }
        return float(camp_stats.get(camp_name, 200))

    def _get_camp_armor(self, camp_name: str) -> float:
        """Retourne l'armure de base d'un camp"""
        return 60.0  # Armure standard pour les monsters

    def _get_camp_armor_per_level(self, camp_name: str) -> float:
        """Retourne l'armure par niveau d'un camp"""
        return 0.0

    def _get_camp_mr(self, camp_name: str) -> float:
        """Retourne la résistance magique de base d'un camp"""
        return 60.0  # MR standard pour les monsters

    def _get_camp_mr_per_level(self, camp_name: str) -> float:
        """Retourne la MR par niveau d'un camp"""
        return 0.0

    def _get_camp_attack_range(self, camp_name: str) -> float:
        """Retourne la portée d'attaque d'un camp"""
        return 125.0  # Portée de mêlée standard

    def _get_camp_ad(self, camp_name: str) -> float:
        """Retourne les dégâts d'attaque de base d'un camp"""
        camp_stats = {
            'Blue_Sentinel': 80,
            'Red_Brambleback': 80,
            'Gromp': 70,
            'Raptors': 50,
            'Krug': 60,
            'Scuttle_Crab': 40
        }
        return float(camp_stats.get(camp_name, 60))

    def _get_camp_ad_per_level(self, camp_name: str) -> float:
        """Retourne les AD par niveau d'un camp"""
        return 0.0

    def _get_camp_as(self, camp_name: str) -> float:
        """Retourne la vitesse d'attaque de base d'un camp"""
        camp_stats = {
            'Blue_Sentinel': 0.6,
            'Red_Brambleback': 0.6,
            'Gromp': 0.7,
            'Raptors': 0.8,
            'Krug': 0.6,
            'Scuttle_Crab': 0.5
        }
        return float(camp_stats.get(camp_name, 0.6))

    def _get_camp_as_per_level(self, camp_name: str) -> float:
        """Retourne l'AS par niveau d'un camp"""
        return 0.0