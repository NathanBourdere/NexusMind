from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

class MapRegion(BaseModel):
    region_id: str   # ex: "BARON_PIT", "TRI_BUSH_BOT"
    name: str
    
    # Géométrie (Polygone de points x,y)
    # Ton parser vérifiera si les coordonnées d'une entité sont dans ces points
    bounds: List[Tuple[float, float]] 
    
    importance_weight: float # 0.0 à 1.0 (L'importance stratégique de la zone)
    is_objective_zone: bool  # Vrai si c'est un pit de Drake/Nashor
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)