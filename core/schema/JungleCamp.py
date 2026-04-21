from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from core.schema import Stats


class JungleCamp(BaseModel):
    id_camp: str
    name: str
    spawn_time: int        # Secondes (ex: 90 pour les buffs)
    respawn_timer: int     # Secondes (ex: 300 pour les buffs)
    stats: Stats
    # Récompenses (base)
    gold_reward: int
    exp_reward: int
    
    # Position
    side: str # "Blue", "Red", "Neutral"
    location_quadrant: str # "Top_Side", "Bot_Side"
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)