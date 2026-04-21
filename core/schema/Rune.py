from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Rune(BaseModel):
    id_rune: int
    name: str
    key: str # ex: "Conqueror"
    short_desc: str
    long_desc: str
    icon_path: str
    
    # Positionnement
    tree_id: int    # Precision, Domination...
    tree_name: str
    slot_index: int # Keystone = 0, Row 1 = 1, etc.
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)