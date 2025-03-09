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
    message:str

class AddUserRequest(BaseModel):
    name: str
    email: str
    phone: str
    role_id: int
    address: str
    photo: Optional[str] = None

class EditUserRequest(BaseModel):
    name: str
    email: str
    phone: str
    role_id: int
    address: str
    photo: Optional[str] = None

class ListAllUser(BaseModel):
    id_user: int
    name: str
    email: str
    phone: str
    address: str
    client: Organization
    role: Organization
    status: bool


class ListUserResponse(BaseModel):
    meta: MetaResponse
    data: ListAllUser
    status: str
    code: int
    message: str