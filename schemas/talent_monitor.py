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