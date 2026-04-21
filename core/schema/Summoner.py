from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Summoner(BaseModel):
    participant_id: int # 1 à 10 (Format Riot API)
    riot_id: str        # ex: "Hide on bush#KR1"
    team_id: int        # 100 ou 200
    
    # Choix pré-game
    champion_id: str
    summoner_spells: List[str] # ex: ["SummonerFlash", "SummonerTeleport"]
    runes: List[int]           # IDs des runes
    
    ability_upgrade_history: List[str] = Field(default_factory=list) 
    # ^ ex: ["Q", "E", "Q", "W", "Q", "R"]
    
    current_ability_ranks: Dict[str, int] = Field(
        default_factory=lambda: {"Q": 0, "W": 0, "E": 0, "R": 0}
    )
    # État actuel (Dynamique)
    level: int
    kills: int
    deaths: int
    assists: int
    cs_score: int
    vision_score: int
    current_gold: int
    total_gold: int
    
    # Inventaire
    items: List[str] # Liste des IDs d'items possédés
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)