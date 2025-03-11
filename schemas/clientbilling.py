from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Organization(BaseModel):
    id:int
    name:str

class Outlet(BaseModel):
    name:str
    latitude:float
    longitude:float
    address:str

class MetaResponse(BaseModel):
    count:int
    page_count:int
    page_size:int
    page:int

class CreateSuccessResponse(BaseModel):
    message:str

class ListAllClientBilling(BaseModel):
    id: int
    name: str
    address: str
    status: Organization


class ListClientBillingResponse(BaseModel):
    meta: MetaResponse
    data: ListAllClientBilling
    status: str
    code: int
    message: str

class ListDetailBilling(BaseModel):
    id: int
    client_id: int
    date: str
    amount: int
    total_talent: int

class ListDetailBillingResponse(BaseModel):
    meta: MetaResponse
    data: ListDetailBilling
    status: str
    code: int
    message: str