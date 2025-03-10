from pydantic import BaseModel


NoContentResponse = None

class Organization(BaseModel):
    id:int
    name:str

class MetaResponse(BaseModel):
    count:int
    page_count:int
    page_size:int
    page:int
class UnauthorizedResponse(BaseModel):
    meta: MetaResponse
    data: None
    status: str
    code: int
    message: str = "Unauthorized"


class BadRequestResponse(BaseModel):
    meta: MetaResponse
    data: None
    status: str
    code: int
    message: str
# class BadRequestResponse(BaseModel):

#     message: str


class ForbiddenResponse(BaseModel):
    meta: MetaResponse
    data: None
    status: str
    code: int
    message: str = "You don't have permissions to perform this action"


class NotFoundResponse(BaseModel):
    meta: MetaResponse
    data: None
    status: str
    code: int
    message:str = "Not Found"
# class NotFoundResponse(BaseModel):

#     detail: str = "Not found"


class InternalServerErrorResponse(BaseModel):

    error: str


class NotImplementedResponse(BaseModel):
    meta: MetaResponse
    data: None
    status: str
    code: int
    message: str = "Not Yet implemented"

# class CudResponses(BaseModel):
#     message:str
class CudResponses(BaseModel):
    meta: MetaResponse
    data: None
    status: str
    code: int
    message:str = "Sucess"

