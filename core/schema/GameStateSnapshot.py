from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
# from core.schema.Summoner import Summoner
# from core.schema.GameEvent import GameEvent
# from core.schema.MinionWave import MinionWave

class GameStateSnapshot(BaseModel):
    game_id: str
    timestamp: float # Le moment précis de la question (ex: 840.5 secondes)
    
    # État macro
    gold_diff: int # Positif si Team 100 mène, négatif si Team 200
    towers_destroyed_100: int
    towers_destroyed_200: int
    drakes_100: List[str]
    drakes_200: List[str]
    
    # Entités actives à cet instant précis
    summoners: List[Dict[str, Any]]     # Remplacer par List[Summoner] en production
    recent_events: List[Dict[str, Any]] # Les 5 derniers GameEvents
    active_waves: List[Dict[str, Any]]  # List[MinionWave]
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)