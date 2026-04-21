from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class VisionEntity(BaseModel):
    entity_id: str
    entity_type: str # "STEALTH_WARD", "CONTROL_WARD", "FAR_SIGHT", "TRAP" (Teemo/Jhin)
    owner_participant_id: int # ID du joueur (1 à 10)
    team_id: int              # 100 (Bleu) ou 200 (Rouge)
    
    position_x: float
    position_y: float
    vision_radius: float
    
    # Gestion du temps
    time_placed: float # Timestamp en secondes
    duration: float    # -1 si permanent (Control Ward)
    is_alive: bool = True
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)