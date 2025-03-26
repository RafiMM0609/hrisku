from typing import List, Optional
from pydantic import BaseModel

class Organization(BaseModel):
    id:Optional[int]=None
    name:Optional[str]=None
    
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
    note:str

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

class DataLeave(BaseModel):
    id:int
    type:str
    status:Organization
    note:Optional[str]=None
    date_information:Optional[str]=None

class DataLeaveResponse(BaseModel):
    meta: MetaResponse
    data: List[DataLeave]
    status: str
    code: int
    message: str

class DataMenuCheckout(BaseModel):
    outlet : DataOutlet
    user_latitude : float
    user_longitude : float 
    distance : float
    clock_in : str
    clock_out : str

class DataMenuCheckoutResponse(BaseModel):
    meta: MetaResponse
    data: DataMenuCheckout
    status: str
    code: int
    message: str

class HeaderAbsensi(BaseModel):
    total:Optional[int]=0
    hadir:Optional[int]=0
    absen:Optional[int]=0
    sakit:Optional[int]=0
    cuti:Optional[int]=0
    izin:Optional[int]=0
    terlambat:Optional[int]=0
    early_leave:Optional[int]=0
    lembur:Optional[int]=0

class HistoryAbsensi(BaseModel):
    date:str = "22 August 2025"
    clock_in:str
    clock_out:Optional[str]=None
    duration:Optional[str] =None
    outlet:DataOutlet

class DataMenuAbsensi(BaseModel):
    this_month:str = "August 2025"
    header:HeaderAbsensi
    history:Optional[List[HistoryAbsensi]]=[]

class DataMenuAbsensiResponse(BaseModel):
    meta: MetaResponse
    data: DataMenuAbsensi
    status: str
    code: int
    message: str

class CheckAttendance(BaseModel):
    clock_in:Optional[str]=None
    clock_out:Optional[str]=None
    outlet:Optional[Organization]=None
    date:Optional[str]=None

class CheckAttendanceResponse(BaseModel):
    meta: MetaResponse
    data: CheckAttendance
    status: str
    code: int
    message: str