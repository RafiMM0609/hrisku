from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import re

class Organization(BaseModel):
    id:Optional[int]=None
    name:Optional[str]=None

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

class HistoryPaymentData(BaseModel):
    id: str
    date: str  # Format: "December 2024"
    client_id: int
    amount: float
    total_talent: int
    status: Organization
    evidence_payment: str
    @classmethod
    def validate_date(cls, date: str) -> bool:
        # Regex to match "Month YYYY" format
        pattern = r"^(January|February|March|April|May|June|July|August|September|October|November|December) \d{4}$"
        return bool(re.match(pattern, date))

class HistoryPaymentResponse(BaseModel):
    meta: MetaResponse
    data: HistoryPaymentData
    status: str
    code: int
    message: str

class ListDetailKeterangan(BaseModel):
    keterangan: str
    nominal: Optional[float]=None
    jumlah: Optional[float]=None

class ListDetailBillingAction(BaseModel):
    title: Optional[str]=None
    client_id: Optional[int]=None
    client_name: Optional[str]=None
    start_period: Optional[str]=None
    end_period: Optional[str]=None
    detail: Optional[List[ListDetailKeterangan]]=[]

class ListDetailBillingActionResponse(BaseModel):
    meta: MetaResponse
    data: ListDetailBillingAction
    status: str
    code: int
    message: str