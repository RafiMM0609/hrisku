from fastapi import APIRouter, Depends, File, Response, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models import get_db
from core.file import preview_file_from_minio, upload_file_to_minio, download_file, upload_file
from core.responses import (
    Created,
    Unauthorized,
    CudResponse,
    InternalServerError,
    BadRequest,
    common_response,
    Ok,
)
from datetime import datetime
from core.security import get_user_from_jwt_token, oauth2_scheme
from schemas.common import NoContentResponse, InternalServerErrorResponse, UnauthorizedResponse, BadRequestResponse, CudResponschema
from repository import mobile as mobileRepo
from repository import shift as shiftRepo
from schemas.mobile import *
from schemas.shift import *
from settings import MINIO_BUCKET
import os

router = APIRouter(tags=["Mobile"])

@router.post("/checkin",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def checkin(
    data: CheckinRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Endpoint for employee check-in.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        await mobileRepo.add_checkin(db, data, user)
        return common_response(CudResponse(
            message="Success check-in"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/check-location",
    responses={
        "201": {"model": DataOutletResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def check_location_routes(
    latitude:float,
    longitude:float,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Endpoint for employee check-in.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data = await mobileRepo.check_nearest_outlet(
            data_latitude=latitude, 
            data_longitude=longitude, 
            db=db, 
            user=user
        )
        return common_response(Ok(
            message="Success get nearest outlet",
            data=data
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))


@router.post("/checkout",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def checkout(
    data: CheckoutRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Endpoint for employee check-out.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        await mobileRepo.add_checkout(db, data, user)
        return common_response(CudResponse(message="Success check-out"))
    except Exception as e:
        return common_response(BadRequest(message=str(e)))


@router.post("/izin",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def izin_route(
    data: LeaveRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Endpoint for employee leave request.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        await mobileRepo.add_izin(db, data, user)
        return common_response(CudResponse(message="Success add izin"))
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    

@router.get("/today-shift",
    responses={
        "200": {"model": DataShiftResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def shift_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await shiftRepo.get_today_shift(db, user)
        return common_response(Ok(
            message="Success get today shift",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.get("/list-leave",
    responses={
        "200": {"model": DataLeaveResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_leave_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    src: str = None,
):
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await mobileRepo.get_list_leave(db, user, src)
        return common_response(Ok(
            message="Success list leave",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/data-checkout",
    responses={
        "200": {"model": DataMenuCheckoutResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_leave_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await mobileRepo.get_menu_checkout(db, user)
        return common_response(Ok(
            message="Success Data Menu Checkout",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/data-absensi",
    responses={
        "200": {"model": DataMenuAbsensiResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_leave_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await mobileRepo.get_menu_absensi(db, user)
        return common_response(Ok(
            message="Success Data Menu Absensi",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
