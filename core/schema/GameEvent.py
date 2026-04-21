from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class GameEvent(BaseModel):
    event_id: str
    event_type: str # "CHAMPION_KILL", "BUILDING_KILL", "ELITE_MONSTER_KILL", "ITEM_PURCHASE"
    timestamp: float # Seconde exacte de l'événement
    
    # Acteurs (ID de 1 à 10)
    killer_id: Optional[int] = None
    victim_id: Optional[int] = None
    assisting_ids: List[int] = Field(default_factory=list)
    
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # ^ ex: gold_bounty_collected, damage_breakdown