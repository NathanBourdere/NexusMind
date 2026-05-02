"""
DataCache - Cache centralisé pour les données partagées entre parsers
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

# Import des schémas
from core.schema.Champion import Champion
from core.schema.Item import Item
from core.schema.Rune import Rune
from core.schema.JungleCamp import JungleCamp
from core.schema.EpicMonster import EpicMonster
from core.schema.Fruit import Fruit
from core.schema.Structure import Structure
from core.schema.MinionWave import MinionWave
from core.schema.Minions import Minions
from core.schema.StatusEffect import StatusEffect


class DataCache:
    """Cache centralisé pour les données partagées entre parsers"""

    def __init__(self, cache_duration_hours: int = 24):
        self.cache_duration = timedelta(hours=cache_duration_hours)

        # Cache des données
        self._champions: Dict[str, tuple[Champion, datetime]] = {}
        self._items: Dict[str, tuple[Item, datetime]] = {}
        self._runes: Dict[int, tuple[Rune, datetime]] = {}
        self._jungle_camps: Dict[str, tuple[JungleCamp, datetime]] = {}
        self._epic_monsters: Dict[str, tuple[EpicMonster, datetime]] = {}
        self._fruits: Dict[str, tuple[Fruit, datetime]] = {}
        self._structures: Dict[str, tuple[Structure, datetime]] = {}
        self._minion_waves: Dict[str, tuple[MinionWave, datetime]] = {}
        self._minions: Dict[str, tuple[Minions, datetime]] = {}

        # Cache des listes
        self._champion_list: Optional[tuple[List[str], datetime]] = None
        self._item_list: Optional[tuple[List[str], datetime]] = None

    def _is_expired(self, timestamp: datetime) -> bool:
        """Vérifie si le cache est expiré"""
        return datetime.now() - timestamp > self.cache_duration

    def _update_cache(self, cache_dict: Dict, key: str, value: Any) -> None:
        """Met à jour le cache avec une nouvelle valeur"""
        cache_dict[key] = (value, datetime.now())

    # --- Champions ---

    def set_champion(self, champion_name: str, champion: Champion) -> None:
        """Stocke un champion dans le cache"""
        self._update_cache(self._champions, champion_name, champion)

    def get_champion(self, champion_name: str) -> Optional[Champion]:
        """Récupère un champion du cache"""
        if champion_name in self._champions:
            champion, timestamp = self._champions[champion_name]
            if not self._is_expired(timestamp):
                return champion
        return None

    def get_all_champions(self) -> Dict[str, Champion]:
        """Récupère tous les champions non expirés"""
        return {
            name: champion
            for name, (champion, timestamp) in self._champions.items()
            if not self._is_expired(timestamp)
        }

    def set_champion_list(self, champion_names: List[str]) -> None:
        """Stocke la liste des champions"""
        self._champion_list = (champion_names, datetime.now())

    def get_champion_list(self) -> Optional[List[str]]:
        """Récupère la liste des champions"""
        if self._champion_list:
            champion_list, timestamp = self._champion_list
            if not self._is_expired(timestamp):
                return champion_list
        return None

    # --- Items ---

    def set_item(self, item_id: str, item: Item) -> None:
        """Stocke un item dans le cache"""
        self._update_cache(self._items, item_id, item)

    def get_item(self, item_id: str) -> Optional[Item]:
        """Récupère un item du cache"""
        if item_id in self._items:
            item, timestamp = self._items[item_id]
            if not self._is_expired(timestamp):
                return item
        return None

    def get_all_items(self) -> Dict[str, Item]:
        """Récupère tous les items non expirés"""
        return {
            item_id: item
            for item_id, (item, timestamp) in self._items.items()
            if not self._is_expired(timestamp)
        }

    # --- Runes ---

    def set_rune(self, rune_id: int, rune: Rune) -> None:
        """Stocke une rune dans le cache"""
        self._update_cache(self._runes, rune_id, rune)

    def get_rune(self, rune_id: int) -> Optional[Rune]:
        """Récupère une rune du cache"""
        if rune_id in self._runes:
            rune, timestamp = self._runes[rune_id]
            if not self._is_expired(timestamp):
                return rune
        return None

    def get_all_runes(self) -> Dict[int, Rune]:
        """Récupère toutes les runes non expirées"""
        return {
            rune_id: rune
            for rune_id, (rune, timestamp) in self._runes.items()
            if not self._is_expired(timestamp)
        }

    # --- Jungle Camps ---

    def set_jungle_camp(self, camp_id: str, camp: JungleCamp) -> None:
        """Stocke un camp de jungle dans le cache"""
        self._update_cache(self._jungle_camps, camp_id, camp)

    def get_jungle_camp(self, camp_id: str) -> Optional[JungleCamp]:
        """Récupère un camp de jungle du cache"""
        if camp_id in self._jungle_camps:
            camp, timestamp = self._jungle_camps[camp_id]
            if not self._is_expired(timestamp):
                return camp
        return None

    def get_all_jungle_camps(self) -> Dict[str, JungleCamp]:
        """Récupère tous les camps de jungle non expirés"""
        return {
            camp_id: camp
            for camp_id, (camp, timestamp) in self._jungle_camps.items()
            if not self._is_expired(timestamp)
        }

    # --- Epic Monsters ---

    def set_epic_monster(self, monster_id: str, monster: EpicMonster) -> None:
        """Stocke un monster épique dans le cache"""
        self._update_cache(self._epic_monsters, monster_id, monster)

    def get_epic_monster(self, monster_id: str) -> Optional[EpicMonster]:
        """Récupère un monster épique du cache"""
        if monster_id in self._epic_monsters:
            monster, timestamp = self._epic_monsters[monster_id]
            if not self._is_expired(timestamp):
                return monster
        return None

    def get_all_epic_monsters(self) -> Dict[str, EpicMonster]:
        """Récupère tous les monsters épiques non expirés"""
        return {
            monster_id: monster
            for monster_id, (monster, timestamp) in self._epic_monsters.items()
            if not self._is_expired(timestamp)
        }

    # --- Fruits ---

    def set_fruit(self, fruit_id: str, fruit: Fruit) -> None:
        """Stocke un fruit dans le cache"""
        self._update_cache(self._fruits, fruit_id, fruit)

    def get_fruit(self, fruit_id: str) -> Optional[Fruit]:
        """Récupère un fruit du cache"""
        if fruit_id in self._fruits:
            fruit, timestamp = self._fruits[fruit_id]
            if not self._is_expired(timestamp):
                return fruit
        return None

    def get_all_fruits(self) -> Dict[str, Fruit]:
        """Récupère tous les fruits non expirés"""
        return {
            fruit_id: fruit
            for fruit_id, (fruit, timestamp) in self._fruits.items()
            if not self._is_expired(timestamp)
        }

    # --- Structures ---

    def set_structure(self, structure_id: str, structure: Structure) -> None:
        """Stocke une structure dans le cache"""
        self._update_cache(self._structures, structure_id, structure)

    def get_structure(self, structure_id: str) -> Optional[Structure]:
        """Récupère une structure du cache"""
        if structure_id in self._structures:
            structure, timestamp = self._structures[structure_id]
            if not self._is_expired(timestamp):
                return structure
        return None

    def get_all_structures(self) -> Dict[str, Structure]:
        """Récupère toutes les structures non expirées"""
        return {
            structure_id: structure
            for structure_id, (structure, timestamp) in self._structures.items()
            if not self._is_expired(timestamp)
        }

    # --- Minion Waves ---

    def set_minion_wave(self, wave_id: str, wave: MinionWave) -> None:
        """Stocke une vague de minions dans le cache"""
        self._update_cache(self._minion_waves, wave_id, wave)

    def get_minion_wave(self, wave_id: str) -> Optional[MinionWave]:
        """Récupère une vague de minions du cache"""
        if wave_id in self._minion_waves:
            wave, timestamp = self._minion_waves[wave_id]
            if not self._is_expired(timestamp):
                return wave
        return None

    # --- Minions ---

    def set_minions(self, minion_type: str, minions: Minions) -> None:
        """Stocke un type de minions dans le cache"""
        self._update_cache(self._minions, minion_type, minions)

    def get_minions(self, minion_type: str) -> Optional[Minions]:
        """Récupère un type de minions du cache"""
        if minion_type in self._minions:
            minions, timestamp = self._minions[minion_type]
            if not self._is_expired(timestamp):
                return minions
        return None

    # --- Cache Management ---

    def clear_expired(self) -> None:
        """Nettoie les entrées expirées du cache"""
        self._champions = {
            k: v for k, v in self._champions.items()
            if not self._is_expired(v[1])
        }
        self._items = {
            k: v for k, v in self._items.items()
            if not self._is_expired(v[1])
        }
        self._runes = {
            k: v for k, v in self._runes.items()
            if not self._is_expired(v[1])
        }
        # ... faire de même pour les autres caches

    def clear_all(self) -> None:
        """Nettoie tout le cache"""
        self._champions.clear()
        self._items.clear()
        self._runes.clear()
        self._jungle_camps.clear()
        self._epic_monsters.clear()
        self._fruits.clear()
        self._structures.clear()
        self._minion_waves.clear()
        self._minions.clear()
        self._champion_list = None
        self._item_list = None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        return {
            'champions': len(self._champions),
            'items': len(self._items),
            'runes': len(self._runes),
            'jungle_camps': len(self._jungle_camps),
            'epic_monsters': len(self._epic_monsters),
            'fruits': len(self._fruits),
            'structures': len(self._structures),
            'minion_waves': len(self._minion_waves),
            'minions': len(self._minions),
            'cache_duration_hours': self.cache_duration.total_seconds() / 3600
        }


# Instance globale du cache
_global_cache: Optional[DataCache] = None


def get_global_cache() -> DataCache:
    """Retourne l'instance globale du cache"""
    global _global_cache
    if _global_cache is None:
        _global_cache = DataCache()
    return _global_cache


def reset_global_cache() -> None:
    """Réinitialise le cache global"""
    global _global_cache
    _global_cache = None