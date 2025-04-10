from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, validator

class Organization(BaseModel):
    id:int
    name:str
    
class MetaResponse(BaseModel):
    count:int
    page_count:int
    page_size:int
    page:int

class CreateSuccess(BaseModel):
    message:str

class DataNationalHoliday(BaseModel):
    id: Optional[int] = None
    date: Optional[str] = None
    name: Optional[str] = None
    note: Optional[str] = None
    is_national: Optional[bool] = None
class DataNationalHolidayResponse(BaseModel):
    meta: MetaResponse
    data: List[DataNationalHoliday]
    status: str
    code: int
    message: str

class DataHolidayRequest(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    note: Optional[str] = None
    is_national: Optional[bool] = None

    @validator('date')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Date must be in the format 'YYYY-MM-DD'")
class EditDataHolidayRequest(BaseModel):
    data: List[DataHolidayRequest]

class DataHolidayAddRequest(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    note: Optional[str] = None
    is_national: Optional[bool] = None