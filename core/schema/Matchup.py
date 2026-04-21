
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Matchup(BaseModel):
    champion_id_a:str
    champion_id_b:str 
    winrate:float
    win_condition:str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    