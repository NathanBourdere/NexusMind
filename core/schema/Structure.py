from typing import List

from pydantic import BaseModel

from core.schema import Stats

from core.schema.Item import Item


class Structure(BaseModel):
    structure_id : str
    archetype : str # "T2"
    stats:Stats
    map_position:str #"mid"
    items:List[Item]