from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class Fruit(BaseModel):
    id_fruit: str # ex: "BlastCone_TopRiver"
    name: str     # "Pomme de pin explosive", "Fleur de vision"
    fruit_type: str # "BLAST_CONE", "HONEYFRUIT", "SCRYER_BLOOM"
    
    # Timers et position
    spawn_time: int         # Seconde d'apparition initiale
    respawn_timer: int      # Temps de recharge après destruction
    position_x: float
    position_y: float
    location_quadrant: str  # ex: "Top_River", "Red_Jungle_Bot"
    
    # État en jeu (utile pour le Snapshot)
    is_active: bool = True
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # ^ ex: Portée de la vision du Scryer, montant de soin du Honeyfruit