from typing import Any, Dict, Optional
from core.schema import Stats
from pydantic import BaseModel, Field


class EpicMonster(BaseModel):
    id_obj: str
    name: str # Drake, Nashor, Herald, Grubs, Elder
    initial_spawn: int
    respawn_timer: int
    stats: Stats
    # Buffs
    buff_name: str
    buff_effect: str # Description de ce que ça donne
    
    # Expertise
    is_scaling: bool # Le Baron scale en HP/AD avec le temps
    scaling_weights : Optional[Dict[str,tuple]] # AD : (0.63,"120") means ad scales by 63% every 120 seconds
    priority_weight: float # ]0,1[ 
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)