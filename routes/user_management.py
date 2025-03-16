from typing import Optional
from email import utils
from fastapi import (
    APIRouter, 
    Depends, 
    # Request, 
    # BackgroundTasks, 
    # Request, 
    # File, 
    # UploadFile
)
from sqlalchemy.orm import Session
from models import get_db
from core.file import generate_link_download
from models.User import User
from core.security import (
    get_user_from_jwt_token,
)
from core.responses import (
    common_response,
    Ok,
    CudResponse,
    BadRequest,
    Unauthorized,
)
from core.security import (
    generate_jwt_token_from_user,
    oauth2_scheme,
)
from schemas.common import (
    BadRequestResponse,
    UnauthorizedResponse,
    InternalServerErrorResponse,
    CudResponschema,
)
from schemas.user_management import (
    AddUserRequest,
    CreateSuccessResponse,
    ListUserResponse,
    EditUserRequest,
    DetailUserResponse,
)
# from core.file import generate_link_download
from repository import user_management as UserRepo

router = APIRouter(tags=["User Management"])


@router.post("/add",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def add_user_route(
    payload: AddUserRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        valid = await UserRepo.add_user_validator(db, payload)
        if not valid["success"]:
            return common_response(BadRequest(message=valid["errors"]))
        user_data = await UserRepo.add_user(
            db=db,
            payload=payload,
            user=user
        )
        return common_response(CudResponse(
            message="User added!", 
            data={
            "name": user_data.name,
            "role": user_data.roles[0].name,
            },
            meta=[]
        ))
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/list",
    responses={
        "200": {"model": ListUserResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_user_route(
    page:Optional[int]=1,
    page_size:Optional[int]=10,
    src:Optional[str]=None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_data, num_data, num_page = await UserRepo.list_user(
            db=db,
            page=page,
            page_size=page_size,
            src=src,
        )
        return common_response(Ok(
            data=user_data,
            meta={
                "count": num_data,
                "page_count": num_page,
                "page_size": page_size,
                "page": page,
            },
            message="Success get data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.delete("/delete/{id}",
    responses={
        "201": {"model": CreateSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def delete_route(
    id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        data = await UserRepo.delete_user(
            db=db,
            id=id,
            user=user,
        )
        return common_response(Ok(
            message="Success delete data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
@router.put("/update/{id}",
    responses={
        "201": {"model": CreateSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_route(
    id:str,
    payload:EditUserRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        valid = await UserRepo.edit_user_validator(
            db=db, 
            payload=payload, 
            id=id
        )
        if not valid["success"]:
            return common_response(BadRequest(message=valid["errors"]))
        data = await UserRepo.edit_user(
            db=db,
            id=id,
            payload=payload,
            user=user,
        )
        return common_response(Ok(
            message="Success edit data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    

@router.get("/{id}",
    responses={
        "200": {"model": DetailUserResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def detail_user_route(
    id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_data = await UserRepo.detail_user(
            db=db,
            id_user=id,
        )
        return common_response(Ok(
            data=user_data,
            message="Success get data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.put("/status/{id}",
    responses={
        "200": {"model": DetailUserResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def update_status_user_route(
    id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_data = await UserRepo.edit_status_user(
            db=db,
            user=user,
            id_user=id,
        )
        return common_response(Ok(
            data=user_data,
            message="Success edit data user"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))