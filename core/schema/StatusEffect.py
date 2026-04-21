from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class StatusEffect(BaseModel):
    effect_id: str
    name: str
    effect_type: str # "BUFF", "DEBUFF", "HARD_CC", "SOFT_CC"
    
    # Acteurs
    source_participant_id: int
    target_participant_id: int
    
    # Application
    duration: float
    time_applied: float
    stacks: int = 1
    
    # Impact (pour les calculs rapides)
    value_modifier: float # ex: 0.6 pour un soin réduit de 40% (Anti-heal)
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)