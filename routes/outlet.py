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
from schemas.outlet import (
    OutletOptionResponse
)
# from core.file import generate_link_download
from repository import outlet as OutletRepo

router = APIRouter(tags=["Outlet"])


@router.get("/option",
    responses={
        "200": {"model": OutletOptionResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def outlet_option_route(
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
    src: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):  
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        data = await OutletRepo.get_outlets(
            db=db,
            src=src,
            client_id=client_id,
        )
        return common_response(
            CudResponse(
                message="Succes get outlet",
                data=data
                )
            )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))