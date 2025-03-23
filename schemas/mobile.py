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

class DataDummy(BaseModel):
    name:str
    email:str

class DataDummyResponse(BaseModel):
    meta: MetaResponse
    data: DataDummy
    status: str
    code: int
    message: str

class CheckinRequest(BaseModel):
    latitude:float
    longitude:float
    outlet_id:int
    shift_id:int

class CheckoutRequest(BaseModel):
    attendance_id:int
    latitude:float
    longitude:float
    outlet_id:int
    shift_id:int

class LeaveRequest(BaseModel):
    start_date:str
    end_date:str
    note:Optional[str]=None
    evidence:Optional[str]=None
    type:str