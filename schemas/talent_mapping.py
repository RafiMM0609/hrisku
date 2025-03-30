from typing import List, Optional, Dict
from pydantic import BaseModel, validator

class Organization(BaseModel):
    id:int
    name:str

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

class ShiftRequest(BaseModel):
    day: str
    start_time : str = "08:00"
    end_time : str = "15:00"
    
    @validator('day')
    def validate_day(cls, v):
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if v not in valid_days:
            raise ValueError(f"Day must be one of the following: {', '.join(valid_days)}")
        return v

class ShiftEdit(BaseModel):
    id_shift:Optional[str]=None
    day: str
    start_time : str = "08:00"
    end_time : str = "15:00"
    
    @validator('day')
    def validate_day(cls, v):
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if v not in valid_days:
            raise ValueError(f"Day must be one of the following: {', '.join(valid_days)}")
        return v

class ShiftResponse(BaseModel):
    shift_id:str
    day: str
    start_time : str = "08:00"
    end_time : str = "15:00"
    
    @validator('day')
    def validate_day(cls, v):
        valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if v not in valid_days:
            raise ValueError(f"Day must be one of the following: {', '.join(valid_days)}")
        return v

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
    history:Optional[List[HistoryContract]]=None

class DetailTalentMapping(BaseModel):
    talent_id:str
    name:str
    dob:Optional[str]=None
    nik:Optional[str]=None
    email:Optional[str]=None
    phone:Optional[str]=None
    address:Optional[str]=None
    client:Optional[Organization]=None
    outlet:Optional[Organization]=None
    workdays:Optional[int]=None
    shift:Optional[List[ShiftResponse]]=None
    contract:Optional[DataContractManagement]=None

class ContractManagement(BaseModel):
    start_date:str
    end_date:str
    file:Optional[str]=None

class EditContractManagement(BaseModel):
    id:int
    start_date:str
    end_date:str
    file:Optional[str]=None
    

class RegisTalentRequest(BaseModel):
    photo: Optional[str] = None
    name: str
    dob: str = "01-12-2004"
    nik: str
    email: str
    phone: str
    address: str
    client_id : int
    outlet_id : int
    shift: Optional[List[ShiftRequest]] = None
    workdays: Optional[int] = None
    contract: Optional[ContractManagement] = None

class EditTalentRequest(BaseModel):
    photo: Optional[str] = None
    name: str
    dob: str = "01-12-2004"
    nik: str
    email: str
    phone: str
    address: str
    client_id : int
    outlet_id : int
    shift: Optional[List[ShiftEdit]]=None
    workdays: Optional[int]=None
    contract: Optional[EditContractManagement]=None
    
    
class ViewPersonalInformation(BaseModel):
    talent_id : str
    name :str
    role_name : str
    dob : str
    nik : str
    email : str
    phone : str
    address : str
    face_id : Optional[str]=None
    
class ViewMappingInformation(BaseModel):
    client_id : str
    client_name : str
    client_address : str
    outlet_name : str
    outlet_address : str
    outlet_latitude : float
    outlet_longitude : float
    workdays : Optional[int] = None
    workarg : Optional[List[ShiftResponse]]
    contract : Optional[ContractManagement]
    
class ViewTalent(BaseModel):
    personal : ViewPersonalInformation
    mapping : ViewMappingInformation
    
class ViewTalentResponse(BaseModel):
    meta: MetaResponse
    data: ViewTalent
    status: str
    code: int
    message: str

class HistoryContractResponse(BaseModel):
    meta: MetaResponse
    data: HistoryContract
    status: str
    code: int
    message: str

class DataCalenderWorkarr(BaseModel):
    id: int
    emp_id: str  # Added emp_id to match the function output
    emp_name: str
    client_id: int
    outlet_id: int
    day: str
    time_start: str
    time_end: str
    workdays: Optional[int] = None
    created_at: str

class DataCalenderWorkarrResponse(BaseModel):
    meta: MetaResponse
    data: DataCalenderWorkarr
    status: str
    code: int
    message: str