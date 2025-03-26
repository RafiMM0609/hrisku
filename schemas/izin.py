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

class DataIzin(BaseModel):
    id:int
    name:str
    kuota:int

class DataIzinResponse(BaseModel):
    meta: MetaResponse
    data: DataIzin
    status: str
    code: int
    message: str