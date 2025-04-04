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
    basic_salary:Optional[float]=None
    agency_fee:Optional[float]=None
    allowance:Optional[float]=None
    total_deduction:Optional[float]=None
    nett_payment:Optional[float]=None
    due_date:Optional[str]=None

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
    name: Optional[str] = None
    address: Optional[str] = None
    outlet: Optional[List[Outlet]] = None
    basic_salary: Optional[float] = None
    agency_fee: Optional[float] = None
    payment_date:str = "01-12-2999"
    bpjs: Optional[List[AddBpjsRequest]] = None
    allowences: Optional[List[AddAllowencesRequest]] = None
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None
    start_contract: Optional[str] = None #20-12-2023
    end_contract: Optional[str] = None #20-12-2024
    file_contract: Optional[str] = None

class EditClientRequest(BaseModel):
    photo:Optional[str]=None
    name: Optional[str] = None
    address: Optional[str] = None
    outlet: Optional[List[OutletEdit]] = None
    basic_salary: Optional[float] = None
    agency_fee: Optional[float] = None
    payment_date:Optional[str] = None
    bpjs: Optional[List[EditBpjsRequest]] = None
    allowences: Optional[List[EditAllowencesRequest]] = None
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None
    id_contract:Optional[str]=None
    start_contract: Optional[str] = None #20-12-2023
    end_contract: Optional[str] = None #20-12-2024
    file_contract: Optional[str] = None

class ListAllClient(BaseModel):
    id: int
    id_client: int
    name: str
    address: str
    outlet: Optional[List[Organization]]=None


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
    address: Optional[str]=None
    outlet: Optional[List[OutletList]]=None
    basic_salary: Optional[float]=None
    agency_fee: Optional[float]=None
    payment_date:Optional[str] = None
    bpjs: Optional[List[EditBpjsRequest]] = None
    allowences: Optional[List[EditAllowencesRequest]] = None
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None
    id_contract:Optional[str]=None
    start_contract: Optional[str] = None #20-12-2023
    end_contract: Optional[str] = None #20-12-2024
    file_contract: Optional[str] = None

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
    latitude:Optional[float]=None
    longitude:Optional[float]=None

class DataDetailClientSignature(BaseModel):
    name:str
    address:Optional[str]=None
    id_client:str
    outlet:List[OutletList]
    payroll:Optional[PayrollClient]=None
    total_active:Optional[int]=0
    manager_signature:Optional[str] = None
    technical_signature:Optional[str] = None
    cs_person: Optional[str] = None
    cs_number: Optional[str] = None
    cs_email: Optional[str] = None
    contract_date:Optional[str] = None # 1 January 2024 - 31 December 2024
    contract_file:Optional[str] = None # file name

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


