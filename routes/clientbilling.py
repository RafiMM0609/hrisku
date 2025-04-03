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
from schemas.clientbilling import (
    ListClientBillingResponse,
    ListDetailBillingResponse,
    ListDetailBillingActionResponse,
)
# from core.file import generate_link_download
from repository import clientbilling as ClientBilRepo

router = APIRouter(tags=["Client Billing"])


@router.get("/list",
    responses={
        "200": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_cb_route(
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
        data, num_data, num_page = await ClientBilRepo.list_client_billing(
            db=db,
            src=src,
            page=page,
            page_size=page_size,
            user=user,
        )
        return common_response(
            Ok(
                message="Succes get list client biling",
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

@router.get("/list-detail/{id}",
    responses={
        "200": {"model": ListDetailBillingResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_detail_cb_route(
    id:str,
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
        data, num_data, num_page = await ClientBilRepo.list_detail_cb(
            db=db,
            id=id,
            user=user,
            src=src,
            page=page,
            page_size=page_size,
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
    
@router.get("/list-detail/action/{id}",
    responses={
        "200": {"model": ListDetailBillingActionResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_detail_cb_route(
    id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):  
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        data = await ClientBilRepo.list_billing_action(
            db=db,
            id=id,
        )
        return common_response(
            Ok(
                message="Succes get lisy client",
                data=data
            )
            )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))