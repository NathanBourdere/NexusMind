"""
Structure Parser - Données sur les structures (Tourelles, Inhibiteurs, Nexus)
Combine les données statiques de Riot et les données dynamiques de Live API
"""

import requests
from typing import Dict, List, Any, Optional
from core.schema.Structure import Structure
from core.schema.Stats import Stats
from core.schema.Item import Item


class StructureParser:
    """Parser pour les données de structures"""

    def __init__(self):
        self.base_url = "https://ddragon.leagueoflegends.com/cdn/14.1.1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def parse_structure(self, structure_id: str, structure_type: str = "TOWER") -> Optional[Structure]:
        """Parse une structure spécifique"""
        try:
            # Données statiques depuis Riot Data Dragon
            static_data = self._get_static_structure_data(structure_id, structure_type)

            # Créer l'objet Structure
            structure = Structure(
                structure_id=structure_id,
                archetype=structure_type,
                stats=self._create_structure_stats(static_data, structure_type),
                map_position=static_data.get('map_position', 'mid'),
                items=[],  # Les structures n'ont pas d'items
                metadata={
                    'source': 'Riot Data Dragon',
                    'static_data': static_data,
                    'structure_type': structure_type,
                    'is_destroyable': static_data.get('is_destroyable', True),
                    'respawn_time': static_data.get('respawn_time', None)
                }
            )

            return structure

        except Exception as e:
            print(f"Error parsing structure {structure_id}: {e}")
            return None

    def _get_static_structure_data(self, structure_id: str, structure_type: str) -> Dict[str, Any]:
        """Récupère les données statiques depuis Riot Data Dragon"""
        try:
            # Données par défaut basées sur les connaissances du jeu
            structure_configs = {
                'TOWER': {
                    'map_position': 'outer',
                    'is_destroyable': True,
                    'respawn_time': None,
                    'base_hp': 5000,
                    'base_armor': 100,
                    'base_ad': 200,
                    'gold_reward': 300
                },
                'TOWER_INNER': {
                    'map_position': 'inner',
                    'is_destroyable': True,
                    'respawn_time': None,
                    'base_hp': 6000,
                    'base_armor': 120,
                    'base_ad': 250,
                    'gold_reward': 300
                },
                'TOWER_BASE': {
                    'map_position': 'base',
                    'is_destroyable': True,
                    'respawn_time': None,
                    'base_hp': 7000,
                    'base_armor': 150,
                    'base_ad': 300,
                    'gold_reward': 300
                },
                'INHIBITOR': {
                    'map_position': 'base',
                    'is_destroyable': True,
                    'respawn_time': 300,  # 5 minutes
                    'base_hp': 5000,
                    'base_armor': 80,
                    'base_ad': 150,
                    'gold_reward': 50
                },
                'NEXUS': {
                    'map_position': 'base',
                    'is_destroyable': True,
                    'respawn_time': None,
                    'base_hp': 5500,
                    'base_armor': 100,
                    'base_ad': 200,
                    'gold_reward': 50
                }
            }

            return structure_configs.get(structure_type, {
                'map_position': 'mid',
                'is_destroyable': True,
                'respawn_time': None,
                'base_hp': 5000,
                'base_armor': 100,
                'base_ad': 200,
                'gold_reward': 100
            })

        except Exception as e:
            print(f"Error getting static data for {structure_id}: {e}")
            return {}

    def _create_structure_stats(self, static_data: Dict[str, Any], structure_type: str) -> Stats:
        """Crée les stats de la structure"""
        return Stats(
            hp=static_data.get('base_hp', 5000),
            hpperlevel=0.0,
            mp=0.0,
            mpperlevel=0.0,
            movespeed=0.0,
            armor=static_data.get('base_armor', 100),
            armorperlevel=0.0,
            spellblock=static_data.get('base_mr', 100),
            spellblockperlevel=0.0,
            attackrange=static_data.get('attack_range', 750),
            hpregen=0.0,
            hpregenperlevel=0.0,
            mpregen=0.0,
            mpregenperlevel=0.0,
            crit=0.0,
            critperlevel=0.0,
            attackdamage=static_data.get('base_ad', 200),
            attackdamageperlevel=0.0,
            attackspeed=static_data.get('base_as', 0.5),
            attackspeedperlevel=0.0
        )

    def parse_all_structures(self) -> Dict[str, Structure]:
        """Parse toutes les structures par défaut"""
        structures = {}

        # Tourelles extérieures
        for lane in ['TOP', 'MID', 'BOT']:
            for team in ['BLUE', 'RED']:
                structure_id = f"TOWER_{lane}_{team}_OUTER"
                structure = self.parse_structure(structure_id, "TOWER")
                if structure:
                    structures[structure_id] = structure

        # Tourelles intérieures
        for lane in ['TOP', 'MID', 'BOT']:
            for team in ['BLUE', 'RED']:
                structure_id = f"TOWER_{lane}_{team}_INNER"
                structure = self.parse_structure(structure_id, "TOWER_INNER")
                if structure:
                    structures[structure_id] = structure

        # Tourelles de base
        for team in ['BLUE', 'RED']:
            structure_id = f"TOWER_BASE_{team}"
            structure = self.parse_structure(structure_id, "TOWER_BASE")
            if structure:
                structures[structure_id] = structure

        # Inhibiteurs
        for lane in ['TOP', 'MID', 'BOT']:
            for team in ['BLUE', 'RED']:
                structure_id = f"INHIBITOR_{lane}_{team}"
                structure = self.parse_structure(structure_id, "INHIBITOR")
                if structure:
                    structures[structure_id] = structure

        # Nexus
        for team in ['BLUE', 'RED']:
            structure_id = f"NEXUS_{team}"
            structure = self.parse_structure(structure_id, "NEXUS")
            if structure:
                structures[structure_id] = structure

        return structures

    def get_structure_positions(self) -> Dict[str, Dict[str, float]]:
        """Retourne les positions de toutes les structures sur la carte"""
        # Positions approximatives sur la carte Summoner's Rift
        return {
            # Tourelles Blue
            'TOWER_TOP_BLUE_OUTER': {'x': 2500, 'y': 2500},
            'TOWER_MID_BLUE_OUTER': {'x': 4000, 'y': 7500},
            'TOWER_BOT_BLUE_OUTER': {'x': 2500, 'y': 12500},
            'TOWER_TOP_BLUE_INNER': {'x': 3500, 'y': 3500},
            'TOWER_MID_BLUE_INNER': {'x': 5000, 'y': 7500},
            'TOWER_BOT_BLUE_INNER': {'x': 3500, 'y': 11500},
            'TOWER_BASE_BLUE': {'x': 4500, 'y': 7500},

            # Tourelles Red
            'TOWER_TOP_RED_OUTER': {'x': 12500, 'y': 2500},
            'TOWER_MID_RED_OUTER': {'x': 11000, 'y': 7500},
            'TOWER_BOT_RED_OUTER': {'x': 12500, 'y': 12500},
            'TOWER_TOP_RED_INNER': {'x': 11500, 'y': 3500},
            'TOWER_MID_RED_INNER': {'x': 10000, 'y': 7500},
            'TOWER_BOT_RED_INNER': {'x': 11500, 'y': 11500},
            'TOWER_BASE_RED': {'x': 10500, 'y': 7500},

            # Inhibiteurs
            'INHIBITOR_TOP_BLUE': {'x': 1500, 'y': 1500},
            'INHIBITOR_MID_BLUE': {'x': 1500, 'y': 7500},
            'INHIBITOR_BOT_BLUE': {'x': 1500, 'y': 13500},
            'INHIBITOR_TOP_RED': {'x': 13500, 'y': 1500},
            'INHIBITOR_MID_RED': {'x': 13500, 'y': 7500},
            'INHIBITOR_BOT_RED': {'x': 13500, 'y': 13500},

            # Nexus
            'NEXUS_BLUE': {'x': 500, 'y': 7500},
            'NEXUS_RED': {'x': 14500, 'y': 7500}
        }

    def get_structure_by_position(self, x: float, y: float) -> Optional[Structure]:
        """Trouve une structure proche de la position donnée"""
        positions = self.get_structure_positions()

        for structure_id, pos in positions.items():
            distance = ((x - pos['x'])**2 + (y - pos['y'])**2)**0.5
            if distance < 300:  # 300 unités de rayon
                return self.parse_structure(structure_id)

        return None

    def update_structure_from_live_data(self, structure_id: str, live_data: Dict[str, Any]) -> Optional[Structure]:
        """Met à jour une structure avec les données en temps réel"""
        try:
            structure = self.parse_structure(structure_id)
            if not structure:
                return None

            # Mettre à jour les stats avec les données live
            if 'current_hp' in live_data:
                structure.stats.hp = live_data['current_hp']

            if 'is_destroyed' in live_data:
                structure.metadata['is_destroyed'] = live_data['is_destroyed']

            if 'destroy_time' in live_data:
                structure.metadata['destroy_time'] = live_data['destroy_time']

            return structure

        except Exception as e:
            print(f"Error updating structure {structure_id} from live data: {e}")
            return None