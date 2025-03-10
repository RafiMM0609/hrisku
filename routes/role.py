from typing import Optional
from email import utils
from fastapi import APIRouter, Depends, Request, BackgroundTasks, Request, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from asyncpg.exceptions import UniqueViolationError
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
    CudResponses,
)
from schemas.role import (
    ListRoleResponse,
    CreateSuccessResponse,
)
# from core.file import generate_link_download
from repository import role as RoleRepo

router = APIRouter(tags=["Role"])


@router.post("/{role_id}",
    responses={
        "200": {"model": ListRoleResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_role_route(
    role_id:int,
    page: Optional[int] = 1,
    page_size: Optional[int] = 10,
    db: AsyncSession = Depends(get_db)
):  # <-- Perbaikan di sini
    try:
        role_data, num_data, num_page = await RoleRepo.list_role(
            db=db,
            page_size=page_size,
            page=page,
            role_id=role_id,
        )
        return common_response(
            Ok(
                message="Succes get data",
                data=role_data,
                meta={
                    "count": num_data,
                    "page_count": num_page,
                    "page_size": page_size,
                    "page": page,
                    },
                )
            )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))