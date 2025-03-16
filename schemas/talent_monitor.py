from typing import List, Optional, Dict
from pydantic import BaseModel

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
    client:Organization
    outlet:DataOutlet
    workdays:int=5
    workarr:List[DataWorkingArrangement]
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