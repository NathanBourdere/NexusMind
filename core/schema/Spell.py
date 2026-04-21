from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Spell(BaseModel):
    id_spell:str
    name:str
    description:str
    tooltip:str # HTML and <e1> tags
    leveltip:Optional[Dict[str, Any]] = None #label: scaling stats list, effect : scaling values list
    maxrank:int #3 or 5
    cooldown:List[float] # ex :[14,12,10]
    cooldownBurn:str # ex: "14/12/10"
    cost:List[float] # same logic
    costBurn:str
    datavalues:Dict[str,Any] # empty most of the time
    effect: List[List[float]] # carries the raw values in the tooltip
    effectBurn: List[float]
    costType: str # mana, health ?
    maxammo: str # -1 if none
    range: List[int] = Field(alias="range_list")
    srangeBurn: str
    resource: Optional[str] = None
    metadata : Optional[Dict[str, Any]] = Field(default_factory=dict) # a dictionary with hidden stats maybe ?
    
    
    
     