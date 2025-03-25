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

class OutletList(BaseModel):
    id_outlet:Optional[str]=None
    name:str
    total_active:int
    address:str
    latitude:float
    longitude:float
    # cs_name:str
    # cs_email:str
    # cs_phone:str

class PayrollClient(BaseModel):
    basic_salary:float
    agency_fee:float
    allowance:float
    total_deduction:float
    nett_payment:float
    due_date:str   

class OutletEdit(BaseModel):
    id_outlet:Optional[str]=None
    name:str
    latitude:float
    longitude:float
    address:str

class OutletGet(BaseModel):
    id_outlet:str
    name:str
    address:str
    total_active:int
    latitude:float
    longitude:float

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
class EditBpjsRequest(BaseModel):
    id:Optional[int]=None
    name: str
    amount: float
class AddAllowencesRequest(BaseModel):
    name: str
    amount: float
class EditAllowencesRequest(BaseModel):
    id:Optional[int]=None
    name: str
    amount: float

class AddClientRequest(BaseModel):
    photo:Optional[str]=None
    name: str
    address: str
    outlet: List[Outlet]
    basic_salary: float
    agency_fee: float
    payment_date:str = "01-12-2999"
    bpjs: Optional[List[AddBpjsRequest]] = None
    allowences: Optional[List[AddAllowencesRequest]] = None
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None

class EditClientRequest(BaseModel):
    photo:Optional[str]=None
    name: str
    address: str
    outlet: List[OutletEdit]
    basic_salary: float
    agency_fee: float
    payment_date:str = "01-12-2999"
    bpjs: Optional[List[EditBpjsRequest]] = None
    allowences: Optional[List[EditAllowencesRequest]] = None
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

class DetailClient(BaseModel):
    id:str
    photo:Optional[str]=None
    name: str
    address: str
    outlet: Optional[List[OutletList]]=None
    basic_salary: float
    agency_fee: float
    payment_date:str = "01-12-2999"
    bpjs: Optional[List[EditBpjsRequest]] = None
    allowences: Optional[List[EditAllowencesRequest]] = None
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None

class DetailClientResponse(BaseModel):
    meta: MetaResponse
    data: DetailClient
    status: str
    code: int
    message: str

class EditOutletRequest(BaseModel):
    name:Optional[str]=None
    total_active:Optional[str]=None
    address:Optional[str]=None
    latitude:Optional[float]
    longitude:Optional[float]

class DataDetailClientSignature(BaseModel):
    name:str
    address:str
    id_client:str
    outlet:List[OutletList]
    payroll:PayrollClient
    total_active:int
    manager_signature:Optional[str] = None
    technical_signature:Optional[str] = None
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None

class DataDetailClientSignatureResponse(BaseModel):
    meta: MetaResponse
    data: DataDetailClientSignature
    status: str
    code: int
    message: str

class DataClientOption(BaseModel):
    id:int
    id_client:Optional[str]=None
    name:Optional[str]=None
    address:Optional[str]=None

class DataClientOptionResponse(BaseModel):
    meta: MetaResponse
    data: DataClientOption
    status: str
    code: int
    message: str


