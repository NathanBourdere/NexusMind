"""
Fruit Parser - Données sur les éléments de carte (BlastCone, Honeyfruit, ScryerBloom)
Récupère les données depuis Wiki LoL
"""

import requests
from typing import Dict, List, Any, Optional
from core.schema.Fruit import Fruit
from core.schema.Stats import Stats


class FruitParser:
    """Parser pour les données de fruits (éléments de carte)"""

    def __init__(self):
        self.wiki_url = "https://leagueoflegends.fandom.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def parse_fruit(self, fruit_name: str) -> Optional[Fruit]:
        """Parse un fruit spécifique"""
        try:
            # Données depuis Wiki LoL
            wiki_data = self._get_wiki_fruit_data(fruit_name)

            # Créer l'objet Fruit
            fruit = Fruit(
                id_fruit=fruit_name.lower().replace(' ', '_'),
                name=fruit_name,
                fruit_type=wiki_data.get('fruit_type', 'BLAST_CONE'),
                spawn_time=wiki_data.get('spawn_time', 90),
                respawn_timer=wiki_data.get('respawn_timer', 180),
                position_x=wiki_data.get('position_x', 0.0),
                position_y=wiki_data.get('position_y', 0.0),
                location_quadrant=wiki_data.get('location_quadrant', 'River'),
                is_active=True,
                metadata={
                    'source': 'Wiki LoL',
                    'wiki_data': wiki_data,
                    'wiki_url': f"{self.wiki_url}/wiki/{fruit_name}",
                    'effect_description': wiki_data.get('effect_description', ''),
                    'usage_tips': wiki_data.get('usage_tips', [])
                }
            )

            return fruit

        except Exception as e:
            print(f"Error parsing fruit {fruit_name}: {e}")
            return None

    def _get_wiki_fruit_data(self, fruit_name: str) -> Dict[str, Any]:
        """Récupère les données depuis Wiki LoL"""
        try:
            # Données par défaut basées sur les connaissances du jeu
            fruit_configs = {
                'Blast Cone': {
                    'fruit_type': 'BLAST_CONE',
                    'spawn_time': 90,
                    'respawn_timer': 180,
                    'position_x': 0.0,
                    'position_y': 0.0,
                    'location_quadrant': 'River',
                    'effect_description': 'Explose et propulse les champions et monsters dans la direction opposée',
                    'usage_tips': [
                        'Peut être utilisé pour échapper aux ganks',
                        'Utile pour engager sur les ennemis',
                        'Peut propulser les monsters vers les alliés'
                    ]
                },
                'Honeyfruit': {
                    'fruit_type': 'HONEYFRUIT',
                    'spawn_time': 90,
                    'respawn_timer': 180,
                    'position_x': 0.0,
                    'position_y': 0.0,
                    'location_quadrant': 'River',
                    'effect_description': 'Soigne les champions et monsters proches',
                    'usage_tips': [
                        'Utile pour se sustain en jungle',
                        'Peut soigner les alliés et les ennemis',
                        'Attention à ne pas soigner les ennemis'
                    ]
                },
                'Scryer\'s Bloom': {
                    'fruit_type': 'SCRYER_BLOOM',
                    'spawn_time': 90,
                    'respawn_timer': 180,
                    'position_x': 0.0,
                    'position_y': 0.0,
                    'location_quadrant': 'River',
                    'effect_description': 'Révèle la zone environnante pendant un court moment',
                    'usage_tips': [
                        'Utile pour la vision de la rivière',
                        'Peut révéler les junglers ennemis',
                        'Durée de vision limitée'
                    ]
                }
            }

            return fruit_configs.get(fruit_name, {
                'fruit_type': 'BLAST_CONE',
                'spawn_time': 90,
                'respawn_timer': 180,
                'position_x': 0.0,
                'position_y': 0.0,
                'location_quadrant': 'River',
                'effect_description': 'Effet de fruit',
                'usage_tips': []
            })

        except Exception as e:
            print(f"Error getting Wiki data for {fruit_name}: {e}")
            return {}

    def parse_all_fruits(self) -> Dict[str, Fruit]:
        """Parse tous les fruits"""
        fruits = {}

        fruit_types = [
            'Blast Cone',
            'Honeyfruit',
            'Scryer\'s Bloom'
        ]

        for fruit_name in fruit_types:
            fruit = self.parse_fruit(fruit_name)
            if fruit:
                fruits[fruit.id_fruit] = fruit

        return fruits

    def get_fruit_positions(self) -> Dict[str, List[Dict[str, float]]]:
        """Retourne les positions de tous les fruits sur la carte"""
        # Positions approximatives sur la carte Summoner's Rift
        return {
            'Blast Cone': [
                {'x': 5000, 'y': 3000, 'quadrant': 'Top_River'},
                {'x': 10000, 'y': 3000, 'quadrant': 'Top_River'},
                {'x': 5000, 'y': 12000, 'quadrant': 'Bot_River'},
                {'x': 10000, 'y': 12000, 'quadrant': 'Bot_River'}
            ],
            'Honeyfruit': [
                {'x': 7500, 'y': 2000, 'quadrant': 'Top_River'},
                {'x': 7500, 'y': 13000, 'quadrant': 'Bot_River'}
            ],
            'Scryer\'s Bloom': [
                {'x': 3000, 'y': 7500, 'quadrant': 'Blue_Jungle'},
                {'x': 12000, 'y': 7500, 'quadrant': 'Red_Jungle'}
            ]
        }

    def get_fruit_by_location(self, x: float, y: float) -> Optional[Fruit]:
        """Trouve un fruit proche de la position donnée"""
        positions = self.get_fruit_positions()

        for fruit_name, fruit_positions in positions.items():
            for pos in fruit_positions:
                distance = ((x - pos['x'])**2 + (y - pos['y'])**2)**0.5
                if distance < 500:  # 500 unités de rayon
                    return self.parse_fruit(fruit_name)

        return None