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

class CheckoutRequest(BaseModel):
    latitude:float
    longitude:float
    outlet_id:int

class LeaveRequest(BaseModel):
    leave_id: int
    start_date:str
    end_date:str
    note:Optional[str]=None
    evidence:Optional[str]=None

class DataOutlet(BaseModel):
    id:int
    name:str
    address:str
    latitude:float
    longitude:float

class DataOutletResponse(BaseModel):
    meta: MetaResponse
    data: DataOutlet
    status: str
    code: int
    message: str