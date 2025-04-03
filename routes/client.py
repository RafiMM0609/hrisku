from typing import Optional
from email import utils
from fastapi import APIRouter, Depends, Request, BackgroundTasks, Request, File, UploadFile
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
from schemas.client import (
    AddClientRequest,
    EditClientRequest,
    DetailClientResponse,
    DataDetailClientSignatureResponse,
    DataClientOptionResponse,
    ListClientResponse
)
# from core.file import generate_link_download
from repository import client as ClientRepo

router = APIRouter(tags=["Client"])


@router.post("/add",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def add_client_route(
    payload: AddClientRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):  
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        valid = await ClientRepo.add_validator(db, payload)
        if not valid["success"]:
            return common_response(BadRequest(message=valid["errors"]))
        data = await ClientRepo.add_client(
            db=db,
            user=user,
            payload=payload,
            background_tasks=background_tasks,
        )
        return common_response(
            CudResponse(
                message="Succes add client"
                )
            )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
@router.put("/edit/{id}",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def edit_client_route(
    id:str,
    payload: EditClientRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):  
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        valid = await ClientRepo.edit_validator(db=db, payload=payload, id=id)
        if not valid["success"]:
            return common_response(BadRequest(message=valid["errors"]))
        data = await ClientRepo.edit_client(
            client_id=id,
            db=db,
            user=user,
            payload=payload,
            background_tasks=background_tasks,
        )
        return common_response(
            CudResponse(
                message="Succes edit client"
                )
            )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
@router.get("/list",
    responses={
        "200": {"model": ListClientResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_client_route(
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
        data, num_data, num_page = await ClientRepo.list_client(
            db=db,
            src=src,
            page=page,
            page_size=page_size,
            user=user,
        )
        return common_response(
            Ok(
                message="Succes get lisy client",
                meta={
                    "count": num_data,
                    "page_count": num_page,
                    "page_size": page_size,
                    "page": page,
                },
                data=data
            )
            )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.get("/option",
    responses={
        "200": {"model": DataClientOptionResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_option_route(
    src:Optional[str]=None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):  
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        data = await ClientRepo.get_client_options(
            db=db,
            src=src,
        )
        return common_response(
            Ok(
                message="Succes get option client",
                data=data
            )
            )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.delete("/delete/{id}",
    responses={
        "201": {"model": CudResponschema},
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
        data = await ClientRepo.delete_client(
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
    
@router.get("/{id}",
    responses={
        "200": {"model": DetailClientResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def detail_route(
    id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        data = await ClientRepo.detail_client(
            db=db,
            id=id,
        )
        return common_response(Ok(
            message="Success delete data",
            data=data,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/detail/{id}",
    responses={
        "200": {"model": DataDetailClientSignatureResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def detail_detail_route(
    id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        data = await ClientRepo.get_detail_client(
            db=db,
            id_client=id,
        )
        return common_response(Ok(
            message="Success delete data",
            data=data,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))