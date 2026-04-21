from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from core.schema import Stats


class Item(BaseModel):
    id_item: str
    name: str
    description: str  # Le texte HTML moche de Riot
    plaintext: str    # La description courte et propre
    
    # Économie
    gold_total: int
    gold_base: int
    gold_sell: int
    purchasable: bool
    
    # Stats et Composition
    stats: Stats # ex: {"FlatPhysicalDamageMod": 50.0}
    from_items: List[str] = Field(default_factory=list) # Composants (IDs)
    into_items: List[str] = Field(default_factory=list) # Évolutions (IDs)
    
    # Classification
    tags: List[str]
    maps: Dict[str, bool] # Savoir si c'est dispo sur la Faille ou en ARAM
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)