from pydantic import BaseModel
from typing import List

class Mapping(BaseModel):
    source_field: str
    target_table: str
    target_column: str

class MappingRequest(BaseModel):
    mappings: List[Mapping]
