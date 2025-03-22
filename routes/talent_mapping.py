from typing import Optional
from email import utils
from fastapi import (
    APIRouter, 
    Depends, 
    BackgroundTasks, 
    # Request, 
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
from schemas.talent_mapping import (
    CreateSuccessResponse,
    ListUserResponse,
    RegisTalentRequest,
    EditTalentRequest,
    ViewTalent,
)
# from core.file import generate_link_download
from repository import talent_mapping as TalentRepo

router = APIRouter(tags=["Talent Mapping"])
    
@router.post("",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def add_route(
    payload: RegisTalentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        valid = await TalentRepo.add_user_validator(db, payload)
        if not valid["success"]:
            return common_response(BadRequest(message=valid["errors"]))
        user_data = await TalentRepo.add_talent(
            db=db,
            user=user,
            payload=payload,
            background_tasks=background_tasks,
        )
        return common_response(Ok(
            message="Success add data"
            )
        )
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
    
@router.put("/{id}",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def edit_route(
    id:str,
    payload: EditTalentRequest,
    background_tasks:BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        valid = await TalentRepo.edit_user_validator(db, payload, id)
        if not valid["success"]:
            return common_response(BadRequest(message=valid["errors"]))
        user_data = await TalentRepo.edit_talent(
            db=db,
            id_user=id,
            user=user,
            background_tasks=background_tasks,
            payload=payload,
        )
        return common_response(Ok(
            message="Success edit data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/{id}",
    responses={
        "201": {"model": CudResponschema},
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
        user_data = await TalentRepo.detail_talent_mapping(
            db=db,
            id_user=id
        )
        return common_response(Ok(
            message="Success get data",
            data=user_data,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
        
ViewTalentData
@router.get("/view/{talent_id}",
    responses={
        "200": {"model": ViewTalent},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def view_talent_route(
    talent_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        talent_data = await TalentRepo.ViewTalentData(
            db=db,
            talent_id=talent_id
        )
        return common_response(Ok(
            message="Success get data",
            data=talent_data,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))