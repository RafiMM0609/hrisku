from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Organization(BaseModel):
    id:int
    name:str

class OutletOption(BaseModel):
    id:int
    outlet_id:Optional[str] = None
    name:Optional[str] = None
    address:Optional[str] = None
    latitude:Optional[float] = None
    longitude:Optional[float] = None

class MetaResponse(BaseModel):
    count:int
    page_count:int
    page_size:int
    page:int

class OutletOptionResponse(BaseModel):
    meta: MetaResponse
    data: OutletOption
    status: str
    code: int
    message: str