from http.client import HTTPException
import httpx
import os
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models import get_db
from core.mail import send_reset_password_email
from core.file import (
    download_file,
    preview_file_from_minio,
    upload_file,
    upload_file_to_minio,
)
from core.responses import (
    Created,
    Unauthorized,
    CudResponse,
    InternalServerError,
    BadRequest,
    common_response,
    Ok,
)
# from core.myredis import get_data_with_cache
from core.security import (
    get_user_from_jwt_token,
    oauth2_scheme,
    generate_jwt_token_from_user,
)

from schemas.common import (
    NoContentResponse,
    InternalServerErrorResponse,
    UnauthorizedResponse,
    BadRequestResponse,
    CudResponschema,
)
from schemas.nationalholiday import (
    DataNationalHolidayResponse,
    EditDataHolidayRequest,
    DataHolidayRequest,
    DataHolidayAddRequest,
)
from repository import nationalholiday as NationalHolidayRepo

router = APIRouter(tags=["Holiday"])

@router.get("",
    responses={
        "200": {"model": DataNationalHolidayResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_national_holiday(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Client id tolong diisi pake id client yang angka ya, formatnya string biar enak.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data = await NationalHolidayRepo.get_data_national_holiday(
            db,
            user
        )
        return common_response(Ok(
            message="Success get data",
            data=data
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.put(
    "/{id}",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def edit_data_holiday(
    id: str,
    request: DataHolidayRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Client id tolong diisi pake id client yang angka ya, formatnya string biar enak.
    """
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return Unauthorized()

        token = await NationalHolidayRepo.edit_national_holiday(
            db=db, 
            payload=request,
            id=id,
            user=user,
            )
        return common_response(
            Ok(
                message="Success edit data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.post(
    "",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def add_data_holiday(
    client_id: str,
    request: DataHolidayRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Client id tolong diisi pake id client yang angka ya, formatnya string biar enak.
    """
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return Unauthorized()

        token = await NationalHolidayRepo.create_data_national_holiday(
            db=db, 
            payload=request,
            client_id=client_id,
            )
        return common_response(
            Ok(
                message="Success add data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.delete(
    "/{id}",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def delete_data_holiday(
    id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Client id tolong diisi pake id client yang angka ya, formatnya string biar enak.
    """
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return Unauthorized()

        await NationalHolidayRepo.delete_data_national_holiday(
            db=db,
            national_holiday_id=id,
        )
        return common_response(
            Ok(
                message="Success delete data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))