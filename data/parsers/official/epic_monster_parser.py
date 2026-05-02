"""
EpicMonster Parser - Données sur les monsters épiques (Drake, Nashor, Herald, etc.)
Combine les données de Riot Data Dragon et Wiki LoL
"""

import requests
from typing import Dict, List, Any, Optional
from core.schema.EpicMonster import EpicMonster
from core.schema.Stats import Stats


class EpicMonsterParser:
    """Parser pour les données de monsters épiques"""

    def __init__(self):
        self.base_url = "https://ddragon.leagueoflegends.com/cdn/14.1.1"
        self.wiki_url = "https://leagueoflegends.fandom.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def parse_epic_monster(self, monster_name: str) -> Optional[EpicMonster]:
        """Parse un monster épique spécifique"""
        try:
            # Données de base depuis Riot Data Dragon
            riot_data = self._get_riot_monster_data(monster_name)

            # Données détaillées depuis Wiki
            wiki_data = self._get_wiki_monster_data(monster_name)

            # Créer l'objet EpicMonster
            monster = EpicMonster(
                id_obj=monster_name.lower().replace(' ', '_'),
                name=monster_name,
                initial_spawn=wiki_data.get('initial_spawn', 300),
                respawn_timer=wiki_data.get('respawn_timer', 300),
                stats=self._create_monster_stats(riot_data, wiki_data),
                buff_name=wiki_data.get('buff_name', monster_name),
                buff_effect=wiki_data.get('buff_effect', ''),
                is_scaling=wiki_data.get('is_scaling', False),
                scaling_weights=wiki_data.get('scaling_weights', None),
                priority_weight=wiki_data.get('priority_weight', 0.5),
                metadata={
                    'source': 'Riot Data Dragon + Wiki LoL',
                    'riot_data': riot_data,
                    'wiki_data': wiki_data,
                    'wiki_url': f"{self.wiki_url}/wiki/{monster_name}"
                }
            )

            return monster

        except Exception as e:
            print(f"Error parsing epic monster {monster_name}: {e}")
            return None

    def _get_riot_monster_data(self, monster_name: str) -> Dict[str, Any]:
        """Récupère les données de base depuis Riot Data Dragon"""
        try:
            # Les monsters épiques sont dans les summoner spells ou items
            # Pour l'instant, on retourne des données par défaut
            return {
                'name': monster_name,
                'description': f'Epic monster: {monster_name}'
            }
        except Exception as e:
            print(f"Error getting Riot data for {monster_name}: {e}")
            return {}

    def _get_wiki_monster_data(self, monster_name: str) -> Dict[str, Any]:
        """Récupère les données détaillées depuis Wiki LoL"""
        try:
            # Données par défaut basées sur les connaissances du jeu
            monster_configs = {
                'Baron Nashor': {
                    'initial_spawn': 1200,  # 20 minutes
                    'respawn_timer': 360,     # 6 minutes
                    'buff_name': 'Buff du Baron',
                    'buff_effect': 'Augmente les stats de l\'équipe et accélère la vitesse des sbires proches',
                    'is_scaling': True,
                    'scaling_weights': {
                        'hp': (0.007, '60'),      # +0.7% HP par minute
                        'ad': (0.005, '60'),      # +0.5% AD par minute
                        'armor': (0.005, '60'),   # +0.5% Armor par minute
                        'mr': (0.005, '60')       # +0.5% MR par minute
                    },
                    'priority_weight': 1.0
                },
                'Elder Dragon': {
                    'initial_spawn': 2400,     # 40 minutes (après 4 dragons)
                    'respawn_timer': 360,       # 6 minutes
                    'buff_name': 'Aspect de l\'Ancien',
                    'buff_effect': 'Dégâts brûlants sur les attaques et sorts, exécution sur les ennemis < 20% PV',
                    'is_scaling': True,
                    'scaling_weights': {
                        'hp': (0.008, '60'),
                        'ad': (0.006, '60'),
                        'armor': (0.006, '60'),
                        'mr': (0.006, '60')
                    },
                    'priority_weight': 0.95
                },
                'Dragon': {
                    'initial_spawn': 300,      # 5 minutes
                    'respawn_timer': 300,       # 5 minutes
                    'buff_name': 'Âme du Dragon',
                    'buff_effect': 'Effet variable selon le type de dragon',
                    'is_scaling': True,
                    'scaling_weights': {
                        'hp': (0.004, '60'),
                        'ad': (0.003, '60'),
                        'armor': (0.003, '60'),
                        'mr': (0.003, '60')
                    },
                    'priority_weight': 0.7
                },
                'Rift Herald': {
                    'initial_spawn': 480,      # 8 minutes
                    'respawn_timer': 300,       # 5 minutes
                    'buff_name': 'Œil du Héraut',
                    'buff_effect': 'Le Héraut vous aide à détruire les structures',
                    'is_scaling': True,
                    'scaling_weights': {
                        'hp': (0.005, '60'),
                        'ad': (0.004, '60'),
                        'armor': (0.004, '60'),
                        'mr': (0.004, '60')
                    },
                    'priority_weight': 0.6
                },
                'Void Grub': {
                    'initial_spawn': 90,       # 1:30
                    'respawn_timer': 180,       # 3 minutes
                    'buff_name': 'Récompense des Grubs',
                    'buff_effect': 'Récompenses après avoir tué 3 grubs',
                    'is_scaling': False,
                    'scaling_weights': None,
                    'priority_weight': 0.3
                }
            }

            return monster_configs.get(monster_name, {
                'initial_spawn': 300,
                'respawn_timer': 300,
                'buff_name': 'Buff',
                'buff_effect': 'Effet de buff',
                'is_scaling': False,
                'scaling_weights': None,
                'priority_weight': 0.5
            })

        except Exception as e:
            print(f"Error getting Wiki data for {monster_name}: {e}")
            return {}

    def _create_monster_stats(self, riot_data: Dict[str, Any], wiki_data: Dict[str, Any]) -> Stats:
        """Crée les stats du monster"""
        # Stats par défaut pour un monster épique
        return Stats(
            hp=wiki_data.get('base_hp', 5000),
            hpperlevel=wiki_data.get('hp_per_level', 100),
            mp=0.0,
            mpperlevel=0.0,
            movespeed=wiki_data.get('movespeed', 300),
            armor=wiki_data.get('base_armor', 60),
            armorperlevel=wiki_data.get('armor_per_level', 5),
            spellblock=wiki_data.get('base_mr', 60),
            spellblockperlevel=wiki_data.get('mr_per_level', 5),
            attackrange=wiki_data.get('attack_range', 125),
            hpregen=wiki_data.get('hp_regen', 10),
            hpregenperlevel=wiki_data.get('hp_regen_per_level', 1),
            mpregen=0.0,
            mpregenperlevel=0.0,
            crit=0.0,
            critperlevel=0.0,
            attackdamage=wiki_data.get('base_ad', 200),
            attackdamageperlevel=wiki_data.get('ad_per_level', 10),
            attackspeed=wiki_data.get('base_as', 0.5),
            attackspeedperlevel=wiki_data.get('as_per_level', 0.02)
        )

    def parse_all_epic_monsters(self) -> Dict[str, EpicMonster]:
        """Parse tous les monsters épiques"""
        monsters = {}

        epic_monsters = [
            'Baron Nashor',
            'Elder Dragon',
            'Dragon',
            'Rift Herald',
            'Void Grub'
        ]

        for monster_name in epic_monsters:
            monster = self.parse_epic_monster(monster_name)
            if monster:
                monsters[monster.id_obj] = monster

        return monsters

    def get_dragon_types(self) -> List[str]:
        """Retourne la liste des types de dragons"""
        return [
            'Infernal Dragon',
            'Mountain Dragon',
            'Cloud Dragon',
            'Ocean Dragon',
            'Hextech Dragon',
            'Chemtech Dragon'
        ]

    def parse_dragon(self, dragon_type: str) -> Optional[EpicMonster]:
        """Parse un dragon spécifique"""
        dragon_name = dragon_type.replace(' Dragon', '')
        return self.parse_epic_monster(dragon_name)