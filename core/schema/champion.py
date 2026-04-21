from typing import Any, Dict, List, Optional
from core.schema import Passive, Stats
from core.schema.Spell import Spell
from pydantic import BaseModel, Field

class Champion(BaseModel):
    name: str
    title: str
    roles: List[str]
    difficulty: int
    stats: Stats
    passive: Passive
    spells: List[Spell]
    partype: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    summary: Optional[str] = None
    