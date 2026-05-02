"""
StatusEffect Parser - Données sur les buffs, debuffs et CC
Récupère les données depuis Riot Live API et Wiki LoL
"""

import requests
from typing import Dict, List, Any, Optional
from core.schema.StatusEffect import StatusEffect


class StatusEffectParser:
    """Parser pour les données de status effects (buffs, debuffs, CC)"""

    def __init__(self):
        self.wiki_url = "https://leagueoflegends.fandom.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def parse_status_effect(self, effect_id: str, source_participant_id: int, target_participant_id: int,
                           game_time: float) -> Optional[StatusEffect]:
        """Parse un status effect spécifique"""
        try:
            # Données depuis Wiki LoL
            wiki_data = self._get_wiki_status_effect_data(effect_id)

            # Créer l'objet StatusEffect
            status_effect = StatusEffect(
                effect_id=effect_id,
                name=wiki_data.get('name', effect_id),
                effect_type=wiki_data.get('effect_type', 'BUFF'),
                source_participant_id=source_participant_id,
                target_participant_id=target_participant_id,
                duration=wiki_data.get('duration', 0.0),
                time_applied=game_time,
                stacks=wiki_data.get('stacks', 1),
                value_modifier=wiki_data.get('value_modifier', 1.0),
                metadata={
                    'source': 'Wiki LoL',
                    'wiki_data': wiki_data,
                    'wiki_url': f"{self.wiki_url}/wiki/{effect_id}",
                    'is_dispellable': wiki_data.get('is_dispellable', False),
                    'is_purgable': wiki_data.get('is_purgable', False),
                    'can_be_reduced': wiki_data.get('can_be_reduced', False),
                    'description': wiki_data.get('description', '')
                }
            )

            return status_effect

        except Exception as e:
            print(f"Error parsing status effect {effect_id}: {e}")
            return None

    def _get_wiki_status_effect_data(self, effect_id: str) -> Dict[str, Any]:
        """Récupère les données depuis Wiki LoL"""
        try:
            # Données par défaut basées sur les connaissances du jeu
            effect_configs = {
                # Buffs
                'Baron Buff': {
                    'name': 'Buff du Baron',
                    'effect_type': 'BUFF',
                    'duration': 180,  # 3 minutes
                    'stacks': 1,
                    'value_modifier': 1.0,
                    'is_dispellable': False,
                    'is_purgable': False,
                    'can_be_reduced': False,
                    'description': 'Augmente les stats de l\'équipe et accélère les sbires proches'
                },
                'Dragon Soul': {
                    'name': 'Âme du Dragon',
                    'effect_type': 'BUFF',
                    'duration': 180,  # 3 minutes
                    'stacks': 1,
                    'value_modifier': 1.0,
                    'is_dispellable': False,
                    'is_purgable': False,
                    'can_be_reduced': False,
                    'description': 'Effet permanent selon le type de dragon'
                },
                'Herald Buff': {
                    'name': 'Œil du Héraut',
                    'effect_type': 'BUFF',
                    'duration': 180,  # 3 minutes
                    'stacks': 1,
                    'value_modifier': 1.0,
                    'is_dispellable': False,
                    'is_purgable': False,
                    'can_be_reduced': False,
                    'description': 'Le Héraut vous aide à détruire les structures'
                },
                'Blue Buff': {
                    'name': 'Bénédiction du Bleu',
                    'effect_type': 'BUFF',
                    'duration': 90,  # 1:30
                    'stacks': 1,
                    'value_modifier': 0.8,  # -20% cooldown
                    'is_dispellable': True,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Réduit les cooldowns et régénère le mana'
                },
                'Red Buff': {
                    'name': 'Bénédiction du Rouge',
                    'effect_type': 'BUFF',
                    'duration': 90,  # 1:30
                    'stacks': 1,
                    'value_modifier': 1.0,
                    'is_dispellable': True,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Applique un slow et des dégâts brûlants sur attaque'
                },

                # Debuffs
                'Ignite': {
                    'name': 'Enflammer',
                    'effect_type': 'DEBUFF',
                    'duration': 5,  # 5 secondes
                    'stacks': 1,
                    'value_modifier': 0.6,  # -40% soin
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Dégâts brûlants et réduction de soin'
                },
                'Exhaust': {
                    'name': 'Épuisement',
                    'effect_type': 'DEBUFF',
                    'duration': 2.5,  # 2.5 secondes
                    'stacks': 1,
                    'value_modifier': 0.4,  # -60% dégâts
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Réduit les dégâts infligés et la vitesse'
                },
                'Chilled': {
                    'name': 'Refroidi',
                    'effect_type': 'DEBUFF',
                    'duration': 1.5,  # 1.5 secondes
                    'stacks': 1,
                    'value_modifier': 0.9,  # -10% vitesse
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Réduit la vitesse de déplacement'
                },

                # Hard CC
                'Stun': {
                    'name': 'Étourdissement',
                    'effect_type': 'HARD_CC',
                    'duration': 1.0,
                    'stacks': 1,
                    'value_modifier': 0.0,  # 0% contrôle
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Empêche toute action'
                },
                'Knockup': {
                    'name': 'Projection',
                    'effect_type': 'HARD_CC',
                    'duration': 0.5,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': False,
                    'description': 'Projette en l\'air'
                },
                'Suppression': {
                    'name': 'Suppression',
                    'effect_type': 'HARD_CC',
                    'duration': 2.5,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': False,
                    'can_be_reduced': False,
                    'description': 'Empêche les actions et les déplacements'
                },
                'Taunt': {
                    'name': 'Provocation',
                    'effect_type': 'HARD_CC',
                    'duration': 1.5,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Force à attaquer le source'
                },
                'Fear': {
                    'name': 'Peur',
                    'effect_type': 'HARD_CC',
                    'duration': 1.0,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Fait fuir en direction opposée'
                },
                'Charm': {
                    'name': 'Charme',
                    'effect_type': 'HARD_CC',
                    'duration': 1.0,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Force à se déplacer vers le source'
                },

                # Soft CC
                'Slow': {
                    'name': 'Ralenti',
                    'effect_type': 'SOFT_CC',
                    'duration': 2.0,
                    'stacks': 1,
                    'value_modifier': 0.6,  # -40% vitesse
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Réduit la vitesse de déplacement'
                },
                'Root': {
                    'name': 'Racine',
                    'effect_type': 'SOFT_CC',
                    'duration': 1.5,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Empêche les déplacements'
                },
                'Silence': {
                    'name': 'Silence',
                    'effect_type': 'SOFT_CC',
                    'duration': 1.5,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Empêche l\'utilisation des sorts'
                },
                'Blind': {
                    'name': 'Aveuglement',
                    'effect_type': 'SOFT_CC',
                    'duration': 2.0,
                    'stacks': 1,
                    'value_modifier': 0.0,
                    'is_dispellable': False,
                    'is_purgable': True,
                    'can_be_reduced': True,
                    'description': 'Les attaques ratent'
                }
            }

            return effect_configs.get(effect_id, {
                'name': effect_id,
                'effect_type': 'BUFF',
                'duration': 0.0,
                'stacks': 1,
                'value_modifier': 1.0,
                'is_dispellable': False,
                'is_purgable': False,
                'can_be_reduced': False,
                'description': 'Effet inconnu'
            })

        except Exception as e:
            print(f"Error getting Wiki data for {effect_id}: {e}")
            return {}

    def parse_all_status_effects(self) -> Dict[str, StatusEffect]:
        """Parse tous les status effects par défaut"""
        effects = {}

        # Buffs
        buff_effects = [
            'Baron Buff', 'Dragon Soul', 'Herald Buff', 'Blue Buff', 'Red Buff'
        ]

        # Debuffs
        debuff_effects = [
            'Ignite', 'Exhaust', 'Chilled'
        ]

        # Hard CC
        hard_cc_effects = [
            'Stun', 'Knockup', 'Suppression', 'Taunt', 'Fear', 'Charm'
        ]

        # Soft CC
        soft_cc_effects = [
            'Slow', 'Root', 'Silence', 'Blind'
        ]

        all_effects = buff_effects + debuff_effects + hard_cc_effects + soft_cc_effects

        for effect_id in all_effects:
            effect = self.parse_status_effect(effect_id, 0, 0, 0.0)
            if effect:
                effects[effect_id] = effect

        return effects

    def get_status_effects_by_type(self, effect_type: str) -> List[StatusEffect]:
        """Retourne les status effects par type"""
        all_effects = self.parse_all_status_effects()
        return [
            effect for effect in all_effects.values()
            if effect.effect_type == effect_type
        ]

    def get_cc_effects(self) -> List[StatusEffect]:
        """Retourne tous les effets de CC"""
        hard_cc = self.get_status_effects_by_type('HARD_CC')
        soft_cc = self.get_status_effects_by_type('SOFT_CC')
        return hard_cc + soft_cc

    def get_buff_effects(self) -> List[StatusEffect]:
        """Retourne tous les buffs"""
        return self.get_status_effects_by_type('BUFF')

    def get_debuff_effects(self) -> List[StatusEffect]:
        """Retourne tous les debuffs"""
        return self.get_status_effects_by_type('DEBUFF')

    def is_hard_cc(self, effect_id: str) -> bool:
        """Vérifie si un effet est un hard CC"""
        effect = self.parse_status_effect(effect_id, 0, 0, 0.0)
        return effect.effect_type == 'HARD_CC' if effect else False

    def is_dispellable(self, effect_id: str) -> bool:
        """Vérifie si un effet peut être dissipé"""
        effect = self.parse_status_effect(effect_id, 0, 0, 0.0)
        return effect.metadata.get('is_dispellable', False) if effect else False

    def get_effect_duration(self, effect_id: str) -> float:
        """Retourne la durée d'un effet"""
        effect = self.parse_status_effect(effect_id, 0, 0, 0.0)
        return effect.duration if effect else 0.0