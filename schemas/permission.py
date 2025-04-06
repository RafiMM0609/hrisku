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

class PermissionSchema(BaseModel):
    id: int
    name: str
    isact: bool
class RolePermissionSchema(BaseModel):
    name: str
    permissions: List[PermissionSchema]
class RolePermissionResponse(BaseModel):
    meta: MetaResponse
    data: List[RolePermissionSchema]
    status: str
    code: int
    message: str