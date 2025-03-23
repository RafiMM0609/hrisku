from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import re

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
    id: str
    date: str  # Format: "December 2024"
    client_id: int
    amount: float
    total_talent: int
    status: Organization
    evidence_payment: str
    verify: Optional[bool]=False
    @classmethod
    def validate_date(cls, date: str) -> bool:
        # Regex to match "Month YYYY" format
        pattern = r"^(January|February|March|April|May|June|July|August|September|October|November|December) \d{4}$"
        return bool(re.match(pattern, date))

class ListDetailBillingResponse(BaseModel):
    meta: MetaResponse
    data: ListDetailBilling
    status: str
    code: int
    message: str

class ListDetailKeterangan(BaseModel):
    keterangan: str
    nominal: Optional[float]=None
    jumlah: Optional[float]=None

class ListDetailBillingAction(BaseModel):
    title: str
    client_id: int
    client_name: str
    start_period: str
    end_period: str
    detail: List[ListDetailKeterangan]

class ListDetailBillingActionResponse(BaseModel):
    meta: MetaResponse
    data: ListDetailBillingAction
    status: str
    code: int
    message: str