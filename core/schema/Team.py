from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Team(BaseModel):
    team_id: int              # 100 (Blue) / 200 (Red)
    participant_ids: List[int] # Les 5 joueurs de l'équipe
    
    # Économie et Objectifs
    total_gold: int
    tower_count: int
    inhibitor_count: int
    inhibitor_timers: Dict[str, float] = Field(default_factory=dict) # Temps restant avant repop
    
    # Buffs globaux
    baron_buff_active: bool = False
    baron_timer_remaining: float = 0.0
    dragon_soul_type: Optional[str] = None # "Infernal", "Hextech", etc.
    grubs_count: int = 0
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # ^ Ici : Win probability actuelle, power spikes d'équipe