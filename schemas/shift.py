from typing import List, Optional
from pydantic import BaseModel

class Organization(BaseModel):
    id:int
    name:str
    
class MetaResponse(BaseModel):
    count:int
    page_count:int
    page_size:int
    page:int

class CreateSuccess(BaseModel):
    message:str

class DataShift(BaseModel):
    id:int
    day:str
    start:str
    end:str

class DataShiftResponse(BaseModel):
    meta: MetaResponse
    data: DataShift
    status: str
    code: int
    message: str