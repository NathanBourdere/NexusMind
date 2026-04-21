from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SummonerSpell(BaseModel):
    id_spell: str      # ex: "SummonerFlash"
    name: str          # "Saut éclair"
    description: str
    cooldown: float    # Temps de recharge de base
    Srange: float       # Portée (ex: 400 pour le Flash)
    
    # Données spécifiques
    summoner_level: int # Niveau requis pour l'avoir
    modes: List[str]    # ["CLASSIC", "ARAM"]
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # ^ Ici : Dégâts d'Ignite scaling, réduction de soin, etc.