from typing import List, Optional
from pydantic import BaseModel

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

class DetailPermission(BaseModel):
    id: int
    permission: str
    module: Organization

class ListAllRole(BaseModel):
    id: int
    name: str
    total_user: str
    permision: List[DetailPermission]
    status: bool

class ListRoleResponse(BaseModel):
    meta: MetaResponse
    data: ListAllRole
    status: str
    code: int
    message: str

class CreateSuccessResponse(BaseModel):
    meta: MetaResponse
    data: CreateSuccess
    status: str
    code: int
    message: str

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

class DetailRole(BaseModel):
    id_role: int
    role_name:str
    permision: DetailPermission
    total_user:int