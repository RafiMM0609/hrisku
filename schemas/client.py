from typing import List, Optional, Dict, Any
from pydantic import BaseModel,condecimal

class Organization(BaseModel):
    id:int
    name:str

class CreateSuccessResponse(BaseModel):
    message:str

class AddBpjsRequest(BaseModel):
    name: str
    fee: int
class AddAllowencesRequest(BaseModel):
    name: str
    amount: int

class AddClientRequest(BaseModel):
    name: str
    address: str
    outlet: List[int]
    basic_salary: str
    agency_fee: condecimal(max_digits=10, decimal_places=2)
    payment_date: date
    bpjs: List[AddBpjsRequest]
    allowences: List[AddAllowencesRequest]

class EditClientRequest(BaseModel):
    name: str
    address: str
    outlet: List[int]
    basic_salary: str
    agency_fee: str
    payment_date: date
    bpjs: List[AddBpjsRequest]
    allowences: List[AddAllowencesRequest]

class ListAllClient(BaseModel):
    id: int
    id_client: int
    name: str
    address: str
    outlet: List[Organization]


class ListClientResponse(BaseModel):
    meta: any,
    data: ListAllClient,
    status: str,
    code: int,
    message: str

class ListAllClientBilling(BaseModel):
    id: int
    id_client: int
    name: str
    address: str
    status: Organization

class ListClientBillingResponse(BaseModel):
    meta: any,
    data: ListAllClientBilling,
    status: str,
    code: int,
    message: str

class ListDetailClientBilling(BaseModel):
    month: int
    talent_resource: str
    billing: str

class ListClientBillingResponse(BaseModel):
    meta: any,
    data: ListDetailClientBilling,
    status: str,
    code: int,
    message: str