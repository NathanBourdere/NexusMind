"""
Riot Static Parser - Data Dragon
Récupère les données statiques de l'API Riot Data Dragon
"""

import requests
import json
from typing import Dict, List, Any, Optional
from core.schema.Champion import Champion
from core.schema.Spell import Spell
from core.schema.Stats import Stats
from core.schema.Passive import Passive
from core.schema.Item import Item
from core.schema.Rune import Rune
from core.schema.SummonerSpell import SummonerSpell


class RiotStaticParser:
    """Parser pour les données statiques de Riot (Data Dragon)"""

    def __init__(self, version: str = "14.1.1", locale: str = "en_US"):
        self.base_url = f"https://ddragon.leagueoflegends.com/cdn/{version}"
        self.version = version
        self.locale = locale
        self.session = requests.Session()

    def _get_json(self, endpoint: str) -> Dict[str, Any]:
        """Récupère les données JSON depuis l'API"""
        url = f"{self.base_url}/data/{self.locale}/{endpoint}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def parse_champion(self, champion_name: str) -> Optional[Champion]:
        """Parse un champion spécifique"""
        try:
            data = self._get_json(f"champion/{champion_name}.json")
            champion_data = data['data'][champion_name]

            # Parse stats
            stats = Stats(**champion_data['stats'])

            # Parse passive
            passive = Passive(
                name=champion_data['passive']['name'],
                description=champion_data['passive']['description']
            )

            # Parse spells
            spells = []
            for spell_data in champion_data['spells']:
                spell = Spell(
                    name=spell_data['name'],
                    description=spell_data['description'],
                    cooldown=spell_data.get('cooldownBurn', '0'),
                    cost=spell_data.get('costBurn', '0'),
                    range=spell_data.get('rangeBurn', '0')
                )
                spells.append(spell)

            # Create champion
            champion = Champion(
                name=champion_data['name'],
                title=champion_data['title'],
                roles=champion_data['tags'],
                difficulty=champion_data['info']['difficulty'],
                stats=stats,
                passive=passive,
                spells=spells,
                partype=champion_data['partype'],
                metadata={
                    'source': 'Riot Data Dragon',
                    'version': self.version,
                    'blurb': champion_data['blurb'],
                    'allytips': champion_data.get('allytips', []),
                    'enemytips': champion_data.get('enemytips', []),
                    'image': champion_data['image']
                }
            )

            return champion

        except Exception as e:
            print(f"Error parsing champion {champion_name}: {e}")
            return None

    def parse_all_champions(self) -> Dict[str, Champion]:
        """Parse tous les champions"""
        try:
            data = self._get_json("champion.json")
            champions = {}

            for champion_name, champion_data in data['data'].items():
                champion = self.parse_champion(champion_name)
                if champion:
                    champions[champion_name] = champion

            return champions

        except Exception as e:
            print(f"Error parsing all champions: {e}")
            return {}

    def parse_item(self, item_id: str) -> Optional[Item]:
        """Parse un item spécifique"""
        try:
            data = self._get_json("item.json")
            item_data = data['data'].get(item_id)

            if not item_data:
                return None

            # Parse stats
            stats_dict = {}
            for key, value in item_data.items():
                if key.startswith('Flat') or key.startswith('Percent') or key.startswith('r'):
                    try:
                        stats_dict[key] = float(value)
                    except (ValueError, TypeError):
                        pass

            stats = Stats(**{k: v for k, v in stats_dict.items() if k in Stats.model_fields})

            # Create item
            item = Item(
                id_item=item_id,
                name=item_data['name'],
                description=item_data.get('description', ''),
                plaintext=item_data.get('plaintext', ''),
                gold_total=item_data.get('gold', {}).get('total', 0),
                gold_base=item_data.get('gold', {}).get('base', 0),
                gold_sell=item_data.get('gold', {}).get('sell', 0),
                purchasable=item_data.get('gold', {}).get('purchasable', True),
                stats=stats,
                from_items=item_data.get('from', []),
                into_items=item_data.get('into', []),
                tags=item_data.get('tags', []),
                maps=item_data.get('maps', {}),
                metadata={
                    'source': 'Riot Data Dragon',
                    'version': self.version,
                    'colloq': item_data.get('colloq', ''),
                    'consumed': item_data.get('consumed', False),
                    'stacks': item_data.get('stacks', 0),
                    'depth': item_data.get('depth', 0),
                    'image': item_data.get('image', {})
                }
            )

            return item

        except Exception as e:
            print(f"Error parsing item {item_id}: {e}")
            return None

    def parse_all_items(self) -> Dict[str, Item]:
        """Parse tous les items"""
        try:
            data = self._get_json("item.json")
            items = {}

            for item_id, item_data in data['data'].items():
                # Skip special items
                if item_id in ['0', '3632', '3631', '3630']:
                    continue

                item = self.parse_item(item_id)
                if item:
                    items[item_id] = item

            return items

        except Exception as e:
            print(f"Error parsing all items: {e}")
            return {}

    def parse_rune(self, rune_id: int) -> Optional[Rune]:
        """Parse une rune spécifique"""
        try:
            data = self._get_json("runesReforged.json")

            for tree in data:
                for slot in tree['slots']:
                    for rune in slot['runes']:
                        if rune['id'] == rune_id:
                            return Rune(
                                id_rune=rune['id'],
                                name=rune['name'],
                                key=rune.get('key', ''),
                                short_desc=rune.get('shortDesc', ''),
                                long_desc=rune.get('longDesc', ''),
                                icon_path=rune.get('icon', ''),
                                tree_id=tree['id'],
                                tree_name=tree['name'],
                                slot_index=slot['slotIndex'],
                                metadata={
                                    'source': 'Riot Data Dragon',
                                    'version': self.version
                                }
                            )

            return None

        except Exception as e:
            print(f"Error parsing rune {rune_id}: {e}")
            return None

    def parse_all_runes(self) -> Dict[int, Rune]:
        """Parse toutes les runes"""
        try:
            data = self._get_json("runesReforged.json")
            runes = {}

            for tree in data:
                for slot in tree['slots']:
                    for rune in slot['runes']:
                        rune_obj = Rune(
                            id_rune=rune['id'],
                            name=rune['name'],
                            key=rune.get('key', ''),
                            short_desc=rune.get('shortDesc', ''),
                            long_desc=rune.get('longDesc', ''),
                            icon_path=rune.get('icon', ''),
                            tree_id=tree['id'],
                            tree_name=tree['name'],
                            slot_index=slot['slotIndex'],
                            metadata={
                                'source': 'Riot Data Dragon',
                                'version': self.version
                            }
                        )
                        runes[rune['id']] = rune_obj

            return runes

        except Exception as e:
            print(f"Error parsing all runes: {e}")
            return {}

    def parse_summoner_spell(self, spell_id: str) -> Optional[SummonerSpell]:
        """Parse un sort d'invocateur"""
        try:
            data = self._get_json("summoner.json")
            spell_data = data['data'].get(spell_id)

            if not spell_data:
                return None

            return SummonerSpell(
                id_spell=spell_id,
                name=spell_data['name'],
                description=spell_data['description'],
                cooldown=spell_data.get('cooldownBurn', '0'),
                Srange=spell_data.get('rangeBurn', '0'),
                summoner_level=spell_data.get('summonerLevel', 1),
                modes=spell_data.get('modes', []),
                metadata={
                    'source': 'Riot Data Dragon',
                    'version': self.version,
                    'image': spell_data.get('image', {})
                }
            )

        except Exception as e:
            print(f"Error parsing summoner spell {spell_id}: {e}")
            return None

    def parse_all_summoner_spells(self) -> Dict[str, SummonerSpell]:
        """Parse tous les sorts d'invocateur"""
        try:
            data = self._get_json("summoner.json")
            spells = {}

            for spell_id, spell_data in data['data'].items():
                spell = self.parse_summoner_spell(spell_id)
                if spell:
                    spells[spell_id] = spell

            return spells

        except Exception as e:
            print(f"Error parsing all summoner spells: {e}")
            return {}

    def get_latest_version(self) -> str:
        """Récupère la dernière version disponible"""
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            response = self.session.get(url)
            response.raise_for_status()
            versions = response.json()
            return versions[0] if versions else self.version
        except Exception as e:
            print(f"Error getting latest version: {e}")
            return self.version