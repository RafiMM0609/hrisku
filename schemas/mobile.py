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
    id:int
    date:str = "22 August 2025"
    time:Optional[str]=None
    activity:Optional[str] = None
    outlet:DataOutlet

class HistoryAbsensi_Menuabsensi(BaseModel):
    id: int
    date:str = "22 August 2025"
    clock_in:str
    clock_out:Optional[str]=None
    duration:Optional[str] =None
    outlet:DataOutlet

class DataMenuAbsensi(BaseModel):
    this_month:str = "August 2025"
    header:HeaderAbsensi
    history:Optional[List[HistoryAbsensi_Menuabsensi]]=[]

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

class DataHeaderTimeSheet(BaseModel):
    start_shift:Optional[str]=None
    end_shift:Optional[str]=None
    total_jam:Optional[int]=None
class CoCiTimesheet(BaseModel):
    id:int
    start_shift:Optional[str]=None
    end_shift:Optional[str]=None
    note:Optional[str]=None
    outlet:Optional[DataOutlet]=None
class ListTimesheet(BaseModel):
    date:str
    coci:CoCiTimesheet
    total_jam:Optional[int]=None
class DataMenuTimeSheet(BaseModel):
    header: Optional[DataHeaderTimeSheet]=None
    calender: List[str]=['2025-08-01', '2025-08-02', '2025-08-03']
    activity: Optional[List[ListTimesheet]]=[]
class DataMenuTimeSheetResponse(BaseModel):
    meta: MetaResponse
    data: DataMenuTimeSheet
    status: str
    code: int
    message: str

class DetailTimesheet(BaseModel):
    work_type: Optional[str]=None
    work_day: Optional[str]=None
    work_hours: Optional[str]=None
    work_model: Optional[str]=None
    history:Optional[List[HistoryAbsensi]]=[]
class DetailTimesheetResponse(BaseModel):
    meta: MetaResponse
    data: DetailTimesheet
    status: str
    code: int
    message: str

class DetailDataAbsensi(BaseModel):
    work_type: Optional[str]=None
    work_day: Optional[str]=None
    work_hours: Optional[str]=None
    work_model: Optional[str]=None
    history:Optional[List[HistoryAbsensi]]=[]
class DetailDataAbsensiResponse(BaseModel):
    meta: MetaResponse
    data: DetailTimesheet
    status: str
    code: int
    message: str

class ListPayroll(BaseModel):
    """
    semua data dibuat optional dengan defailt value None atau []
    """
    id:Optional[int]=None
    date:Optional[str]=None # March 2025
    performance:Optional[str]=None # You doing great 10/10
    utilization:Optional[str]=None # 100%
    net_salary:Optional[str]=None # 1.000.000
class ListPayrollResponse(BaseModel):
    meta: MetaResponse
    data: List[ListPayroll]
    status: str
    code: int
    message: str

class DetailPayroll(BaseModel):
    """
    semua data dibuat optional dengan defailt value None atau []
    """
    date:Optional[str]=None # March 2025
    client_name:Optional[str]=None # PT. ABC
    client_address:Optional[str]=None # Jl. ABC No. 1
    client_code:Optional[str]=None # ABC123
    outlet_name:Optional[str]=None # Outlet ABC
    outlet_address:Optional[str]=None # Jl. ABC No. 1
    outlet_latitude:Optional[float]=None # -6.123456
    outlet_longitude:Optional[float]=None # 106.123456
    download_link:Optional[str]=None # https://example.com/download
class DetailPayrollResponse(BaseModel):
    meta: MetaResponse
    data: DetailPayroll
    status: str
    code: int
    message: str
