from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Passive(BaseModel):
    name: str
    description: str
    # metadata ici pour les cooldowns internes (souvent pas dans le JSON)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)