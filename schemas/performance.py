from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Organization(BaseModel):
    id:Optional[int]=None
    name:Optional[str]=None

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

class PerformanceRequest(BaseModel):
    emp_id: str
    softskill: Optional[int]=0
    hardskill: Optional[int]=0
    note: Optional[str]=None

class EditPerformanceRequest(BaseModel):
    softskill: Optional[int]=0
    hardskill: Optional[int]=0
    note: Optional[str]=None