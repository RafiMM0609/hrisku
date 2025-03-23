from fastapi import APIRouter, Depends, File, Response, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models import get_db
from core.file import preview_file_from_minio, upload_file_to_minio, download_file, upload_file
from core.responses import (
    Created,
    Unauthorized,
    common_response,
    InternalServerError,
    BadRequest,
)
from datetime import datetime
from core.security import get_user_from_jwt_token, oauth2_scheme
from schemas.common import NoContentResponse, InternalServerErrorResponse, UnauthorizedResponse
from repository import mobile as mobileRepo
from schemas.mobile import *
from settings import MINIO_BUCKET
import os

router = APIRouter(tags=["Mobile"])

@router.post("/checkin", response_model=NoContentResponse)
async def checkin(
    data: CheckinRequest,
    db: Session = Depends(get_db),
    user=Depends(get_user_from_jwt_token),
):
    """
    Endpoint for employee check-in.
    """
    if not user:
        return Unauthorized()
    try:
        await mobileRepo.add_chekin(db, data, user)
        return NoContentResponse()
    except ValueError as e:
        return BadRequest(detail=str(e))
    except Exception as e:
        return InternalServerError(detail=str(e))


@router.post("/checkout", response_model=NoContentResponse)
async def checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user=Depends(get_user_from_jwt_token),
):
    """
    Endpoint for employee check-out.
    """
    if not user:
        return Unauthorized()
    try:
        await mobileRepo.add_checkout(db, data, user)
        return NoContentResponse()
    except ValueError as e:
        return BadRequest(detail=str(e))
    except Exception as e:
        return InternalServerError(detail=str(e))


@router.post("/izin", response_model=NoContentResponse)
async def izin(
    data: LeaveRequest,
    db: Session = Depends(get_db),
    user=Depends(get_user_from_jwt_token),
):
    """
    Endpoint for employee leave request.
    """
    if not user:
        return Unauthorized()
    try:
        await mobileRepo.add_izin(db, data, user)
        return NoContentResponse()
    except ValueError as e:
        return BadRequest(detail=str(e))
    except Exception as e:
        return InternalServerError(detail=str(e))

