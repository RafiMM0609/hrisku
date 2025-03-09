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
from schemas.user_management import (
    AddUserRequest,
    CreateSuccessResponse,
)
# from core.file import generate_link_download
from repository import user_management as UserRepo

router = APIRouter(tags=["User Management"])


@router.post("/add-user",
    responses={
        "200": {"model": CudResponses},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def add_user_route(
    payload: AddUserRequest,
    db: AsyncSession = Depends(get_db)
):  # <-- Perbaikan di sini
    try:
        user_data = await UserRepo.add_user(db=db, payload=payload)
        return common_response(CudResponse(message="User added!", data=user_data))
    except Exception as e:
        return common_response(BadRequest(message=str(e)))