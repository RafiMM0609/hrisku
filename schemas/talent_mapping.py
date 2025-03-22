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

class ShiftRequest(BaseModel):
    day: str
    start_time : str = "08:00"
    end_time : str = "15:00"
class ShiftEdit(BaseModel):
    id_shift:Optional[str]=None
    day: str
    start_time : str = "08:00"
    end_time : str = "15:00"

class ShiftResponse(BaseModel):
    shift_id:str
    day: str
    start_time : str = "08:00"
    end_time : str = "15:00"

class DetailTalentMapping(BaseModel):
    talent_id:str
    name:str
    dob:str="22-12-31"
    nik:str
    email:str
    phone:str
    address:str
    client:Organization
    outlet:Organization
    workdays:int
    shift:List[ShiftResponse]
    contract:Optional[DataContractManagement]=None

class ContractManagement(BaseModel):
    start_date:str
    end_date:str
    file:Optional[str]=None

class HistoryContract(BaseModel):
    start_date:Optional[str]=None
    end_date:Optional[str]=None
    file:Optional[str]=None
    file_name:Optional[str]=None

class DataContractManagement(BaseModel):
    start_date:Optional[str]=None
    end_date:Optional[str]=None
    file:Optional[str]=None
    history:Optional[HistoryContract]=None
    

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
    shift: Optional[List[ShiftRequest]]
    workdays: Optional[int]
    contract: Optional[ContractManagement]

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
    shift: Optional[List[ShiftEdit]]
    workdays: Optional[int]
