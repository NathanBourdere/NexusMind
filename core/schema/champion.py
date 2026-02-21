from typing import Dict, List, Optional

from pydantic import BaseModel

class Champion(BaseModel):
    name: str
    title: str
    roles: List[str] 
    difficulty: int
    spells: List[Dict]
    metadata: Dict
    summary: Optional[str] = None