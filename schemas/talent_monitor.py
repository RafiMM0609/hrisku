from typing import List, Optional, Dict
from pydantic import BaseModel

class Organization(BaseModel):
    id:int
    name:str

class ClientData(BaseModel):
    id:str
    name:str
    address:str

class MetaResponse(BaseModel):
    count:int
    page_count:int
    page_size:int
    page:int

class CreateSuccessResponse(BaseModel):
    meta: MetaResponse
    data: None
    status: str
    code: int
    message: str

class ListAllUser(BaseModel):
    talent_id: str
    name: str
    dob: str
    nik: str
    email: str
    phone: str
    address: str


class ListUserResponse(BaseModel):
    meta: MetaResponse
    data: ListAllUser
    status: str
    code: int
    message: str

class TalentInformation(BaseModel):
    name:str
    role:Organization
    talent_id:str
    dob:str="31-12-2099"
    phone:str
    address:str
    nik:str
    email:str
    photo:str

class TalentInformationResponse(BaseModel):
    meta: MetaResponse
    data: TalentInformation
    status: str
    code: int
    message: str

class DataOutlet(BaseModel):
    address:str
    name:str
    latitude:float=-6.2088
    longitude:float=106.8456
class DataWorkingArrangement(BaseModel):
    shift_id:str='S001'
    day:str='Monday'
    time_start:str="08:00"
    time_end:str="15:00"
class TalentMapping(BaseModel):
    client:Optional[ClientData]=None
    outlet:Optional[DataOutlet]=None
    workdays:int=0
    workarr:Optional[List[DataWorkingArrangement]]=None
class TalentMappingResponse(BaseModel):
    meta: MetaResponse
    data: TalentMapping
    status: str
    code: int
    message: str

class DataHistorisCont(BaseModel):
    start_cont:str="1 January 2024"
    end_cont:str="16 October 2025"
    name_cont:str
    evidence_cont:str
class DataContrat(BaseModel):
    emp_name:str
    role: Organization
    start_cont:str="1 January 2024"
    end_cont:str="16 October 2025"
    evidence_cont:str
    history_cont:DataHistorisCont

class DataContratResponse(BaseModel):
    meta: MetaResponse
    data: DataContrat
    status: str
    code: int
    message: str

class HistoryContract(BaseModel):
    start_date:Optional[str]=None
    end_date:Optional[str]=None
    file:Optional[str]=None
    file_name:Optional[str]=None

class DataContractManagement(BaseModel):
    id:int
    start_date:Optional[str]=None
    end_date:Optional[str]=None
    file:Optional[str]=None

class ContractManagement(BaseModel):
    talent_id:Optional[str]=None
    talent_name:Optional[str]=None
    talent_role:Optional[str]=None
    contract:Optional[DataContractManagement]=None
    history:Optional[List[HistoryContract]]=None

class ContractManagementResponse(BaseModel):
    meta: MetaResponse
    data: ContractManagement
    status: str
    code: int
    message: str

class AttendanceData(BaseModel):
    total_workdays: int
    id: int
    date : str
    location: Optional[str] = None
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None

class AttendanceGraphData(BaseModel):
    type: str
    desktop: int

class LeaveSubmission(BaseModel):
    total_pending: int
    type: str
    date_period: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    note: Optional[str] = None
    evidence: Optional[str] = None
    file_name: Optional[str] = None
    status: Optional[Organization] = None

class TalentAttendance(BaseModel):
    name: str
    role: Organization
    attendance: List[AttendanceData]
    leave_submission: List[LeaveSubmission]
    graph: List[AttendanceGraphData]

class TalentAttendanceResponse(BaseModel):
    meta: MetaResponse
    data: ContractManagement
    status: str
    code: int
    message: str

class TimeSheetHistory(BaseModel):
    date:Optional[str]=None
    working_hours:int
    notes:Optional[str]=None

class TalentTimesheet(BaseModel):
    name: str
    role_name: str
    total_workdays: int
    timesheet: Optional[List[TimeSheetHistory]]=None

class TalentTimesheetResponse(BaseModel):
    meta: MetaResponse
    data: TalentTimesheet
    status: str
    code: int
    message: str

class PerformanceHistory(BaseModel):
    date:Optional[str]=None
    softskill:Optional[int]=0
    hardskill:Optional[int]=0
    total_point:Optional[str]=None
    notes:Optional[str]=None

class TalentPerformance(BaseModel):
    name: str
    role_name: str
    performance: Optional[str]=None
    history: Optional[List[PerformanceHistory]]=None