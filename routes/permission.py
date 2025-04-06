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
from schemas.permission import (
    RolePermissionResponse
)
from repository import permission as PermissionRepo

router = APIRouter(tags=["Permission"])

@router.get("/{role_id}",
    responses={
        "200": {"model": RolePermissionResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def get_data_table_permission(
    role_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Client id tolong diisi pake id role yang angka ya, formatnya string biar enak.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data = await PermissionRepo.get_data_permission_table(
            db,
            role_id,
        )
        return common_response(Ok(
            message="Success get data",
            data=data
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.put("/{role_permission_id}",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def edit_data_table_permission(
    role_permission_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Client id tolong diisi pake id yang ada di dalem permission yak yang angka ya, formatnya string biar enak.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        await PermissionRepo.edit_permission(
            db,
            role_permission_id,
        )
        return common_response(Ok(
            message="Success edit data",
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))