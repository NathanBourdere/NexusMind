from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class MinionWave(BaseModel):
    lane: str # "TOP", "MID", "BOT"
    
    # L'état macro de la wave
    state: str # "FROZEN", "SLOW_PUSH_BLUE", "HARD_CRASHING_RED", "BOUNCING"
    
    # Composition
    minion_count_blue: int
    minion_count_red: int
    has_cannon_blue: bool
    has_cannon_red: bool
    
    # Position moyenne de la collision des waves
    collision_position_x: float
    collision_position_y: float
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # ^ ex: HP total de la wave pour calculer le temps de clear