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

            # Créer les stats (simplifiées)
            stats = Stats(
                hp=100.0,
                hpperlevel=0.0,
                mp=0.0,
                mpperlevel=0.0,
                movespeed=0.0,
                armor=0.0,
                armorperlevel=0.0,
                spellblock=0.0,
                spellblockperlevel=0.0,
                attackrange=0.0,
                hpregen=0.0,
                hpregenperlevel=0.0,
                mpregen=0.0,
                mpregenperlevel=0.0,
                crit=0.0,
                critperlevel=0.0,
                attackdamage=0.0,
                attackdamageperlevel=0.0,
                attackspeed=0.0,
                attackspeedperlevel=0.0
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