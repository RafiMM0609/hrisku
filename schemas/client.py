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

class AddBpjsRequest(BaseModel):
    name: str
    amount: float
class AddAllowencesRequest(BaseModel):
    name: str
    amount: float

class AddClientRequest(BaseModel):
    name: str
    address: str
    outlet: List[Outlet]
    basic_salary: float
    agency_fee: float
    payment_date:str = "01-12-2999"
    bpjs: List[AddBpjsRequest]
    allowences: List[AddAllowencesRequest]
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None

class EditClientRequest(BaseModel):
    name: str
    address: str
    outlet: List[Outlet]
    basic_salary: str
    agency_fee: str
    payment_date: str
    bpjs: List[AddBpjsRequest]
    allowences: List[AddAllowencesRequest]
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None

class ListAllClient(BaseModel):
    id: int
    id_client: int
    name: str
    address: str
    outlet: List[Organization]


class ListClientResponse(BaseModel):
    meta: MetaResponse
    data: ListAllClient
    status: str
    code: int
    message: str

class ListAllClientBilling(BaseModel):
    id: int
    id_client: int
    name: str
    address: str
    status: Organization

class ListClientBillingResponse(BaseModel):
    meta: MetaResponse
    data: ListAllClientBilling
    status: str
    code: int
    message: str

class ListDetailClientBilling(BaseModel):
    month: int
    talent_resource: str
    billing: str

class ListClientBillingResponse(BaseModel):
    meta: MetaResponse
    data: ListDetailClientBilling
    status: str
    code: int
    message: str