from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from core.schema import Stats
from core.schema.Item import Item

class Minions(BaseModel):
    archetype : str # melee, range, super
    respawn_timer : str
    stats: Stats
    metadata : Optional[Dict[str, Any]] = Field(default_factory=dict)
    items:List[Item]