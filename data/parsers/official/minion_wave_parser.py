"""
MinionWave Parser - Données sur les vagues de minions
Combine les données de Wiki LoL et des calculs de gameplay
"""

import requests
from typing import Dict, List, Any, Optional
from core.schema.MinionWave import MinionWave


class MinionWaveParser:
    """Parser pour les données de vagues de minions"""

    def __init__(self):
        self.wiki_url = "https://leagueoflegends.fandom.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Timers d'apparition des vagues (en secondes)
        self.wave_timers = {
            1: 75,    # Première vague à 1:15
            2: 105,   # Deuxième vague à 1:45
            3: 135,   # Troisième vague à 2:15
            # Ensuite toutes les 30 secondes
        }

    def parse_minion_wave(self, lane: str, wave_number: int, game_time: float) -> Optional[MinionWave]:
        """Parse une vague de minions spécifique"""
        try:
            # Calculer l'état de la vague
            wave_state = self._calculate_wave_state(lane, wave_number, game_time)

            # Calculer la composition de la vague
            composition = self._calculate_wave_composition(wave_number)

            # Calculer la position de collision
            collision_position = self._calculate_collision_position(lane, game_time)

            # Créer l'objet MinionWave
            wave = MinionWave(
                lane=lane,
                state=wave_state['state'],
                minion_count_blue=composition['blue_count'],
                minion_count_red=composition['red_count'],
                has_cannon_blue=composition['has_cannon_blue'],
                has_cannon_red=composition['has_cannon_red'],
                collision_position_x=collision_position['x'],
                collision_position_y=collision_position['y'],
                metadata={
                    'source': 'Wiki LoL + Calculs',
                    'wave_number': wave_number,
                    'game_time': game_time,
                    'spawn_time': wave_state['spawn_time'],
                    'cannon_wave': composition['is_cannon_wave'],
                    'super_wave': composition['is_super_wave'],
                    'composition': composition
                }
            )

            return wave

        except Exception as e:
            print(f"Error parsing minion wave for {lane} wave {wave_number}: {e}")
            return None

    def _calculate_wave_state(self, lane: str, wave_number: int, game_time: float) -> Dict[str, Any]:
        """Calcule l'état de la vague"""
        # Calculer le temps d'apparition de la vague
        if wave_number <= 3:
            spawn_time = self.wave_timers.get(wave_number, 75 + (wave_number - 1) * 30)
        else:
            spawn_time = 135 + (wave_number - 3) * 30

        # Déterminer l'état de la vague
        if game_time < spawn_time:
            state = "SPAWNING"
        elif game_time < spawn_time + 30:
            state = "ACTIVE"
        else:
            state = "CLEARED"

        return {
            'state': state,
            'spawn_time': spawn_time,
            'wave_number': wave_number
        }

    def _calculate_wave_composition(self, wave_number: int) -> Dict[str, Any]:
        """Calcule la composition de la vague"""
        # Vagues avec canon
        cannon_waves = [3, 8, 13, 18, 23, 28, 33, 38, 43, 48, 53, 58, 63, 68, 73, 78, 83, 88, 93, 98]

        # Vagues super minions (après destruction d'inhibiteur)
        is_cannon_wave = wave_number in cannon_waves
        is_super_wave = wave_number > 100  # Approximation

        # Composition de base
        blue_count = 6  # 3 melee + 3 caster
        red_count = 6

        if is_cannon_wave:
            blue_count += 1  # +1 canon
            red_count += 1

        if is_super_wave:
            blue_count = 1  # 1 super minion
            red_count = 1

        return {
            'blue_count': blue_count,
            'red_count': red_count,
            'has_cannon_blue': is_cannon_wave,
            'has_cannon_red': is_cannon_wave,
            'is_cannon_wave': is_cannon_wave,
            'is_super_wave': is_super_wave,
            'melee_count': 3 if not is_super_wave else 0,
            'caster_count': 3 if not is_super_wave else 0,
            'cannon_count': 1 if is_cannon_wave else 0,
            'super_count': 1 if is_super_wave else 0
        }

    def _calculate_collision_position(self, lane: str, game_time: float) -> Dict[str, float]:
        """Calcule la position de collision des vagues"""
        # Positions approximatives de collision par lane
        lane_positions = {
            'TOP': {'x': 7500, 'y': 2500},
            'MID': {'x': 7500, 'y': 7500},
            'BOT': {'x': 7500, 'y': 12500}
        }

        base_position = lane_positions.get(lane, {'x': 7500, 'y': 7500})

        # Ajuster la position en fonction du temps (les vagues avancent)
        time_factor = min(game_time / 1800, 1.0)  # Max à 30 minutes

        if lane == 'TOP':
            base_position['y'] += time_factor * 5000
        elif lane == 'BOT':
            base_position['y'] -= time_factor * 5000
        # MID reste relativement central

        return base_position

    def get_next_wave_time(self, current_wave: int) -> float:
        """Retourne le temps de la prochaine vague"""
        if current_wave <= 3:
            return self.wave_timers.get(current_wave + 1, 75 + current_wave * 30)
        else:
            return 135 + (current_wave - 2) * 30

    def get_cannon_waves(self, max_wave: int = 100) -> List[int]:
        """Retourne la liste des vagues avec canon"""
        cannon_waves = []
        for wave in range(1, max_wave + 1):
            if self._calculate_wave_composition(wave)['is_cannon_wave']:
                cannon_waves.append(wave)
        return cannon_waves

    def parse_all_lanes_waves(self, game_time: float, max_wave: int = 20) -> Dict[str, List[MinionWave]]:
        """Parse toutes les vagues pour toutes les lanes"""
        all_waves = {
            'TOP': [],
            'MID': [],
            'BOT': []
        }

        for lane in all_waves.keys():
            for wave_number in range(1, max_wave + 1):
                wave = self.parse_minion_wave(lane, wave_number, game_time)
                if wave:
                    all_waves[lane].append(wave)

        return all_waves

    def get_wave_state_description(self, state: str) -> str:
        """Retourne une description de l'état de la vague"""
        descriptions = {
            'SPAWNING': 'Les minions sont en train d\'apparaître',
            'ACTIVE': 'Les minions sont en train de se battre',
            'CLEARED': 'La vague a été nettoyée',
            'FROZEN': 'La vague est gelée (slow push)',
            'SLOW_PUSH_BLUE': 'Slow push en faveur de Blue',
            'SLOW_PUSH_RED': 'Slow push en faveur de Red',
            'HARD_CRASHING_BLUE': 'Hard crash vers la base Blue',
            'HARD_CRASHING_RED': 'Hard crash vers la base Red',
            'BOUNCING': 'Les vagues rebondissent'
        }
        return descriptions.get(state, 'État inconnu')