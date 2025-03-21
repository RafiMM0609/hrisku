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
from schemas.talent_monitor import (
    CreateSuccessResponse,
    ListUserResponse,
    TalentInformationResponse,
    TalentMappingResponse,
    DataContratResponse
)
# from core.file import generate_link_download
from repository import talent_monitor as TalentRepo

router = APIRouter(tags=["Talent Monitor"])
    
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
        user_data, num_data, num_page = await TalentRepo.list_talent(
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
    
@router.get("/information/{talent_id}",
    responses={
        "200": {"model": TalentInformationResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def detail_user_information_route(
    talent_id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_data = await TalentRepo.data_talent_information(
            db=db,
            talent_id=talent_id
        )
        return common_response(Ok(
            data=user_data,
            message="Success get data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))