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
from settings import MINIO_BUCKET
import os

router = APIRouter(tags=["File"])


@router.post(
    "/upload",
    responses={
        "204": {"model": NoContentResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def upload_file_router(
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized(message="Invalid/Expired token"))
        file_extension = os.path.splitext(file.filename)[1]
        file_name = os.path.splitext(file.filename)[0]
        now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        path = await upload_file(
            upload_file=file, path=f"/tmp/{str(file_name).replace(' ','_')}-{user.name}{now.replace(' ','_')}{file_extension}"
        )
        return common_response(Created(path))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return common_response(BadRequest(error="Failed Upload", detail=str(e)))


@router.get(
    "/download",
    response_class=FileResponse or UnauthorizedResponse
)
async def dowload_file(
    minio_path: str,
):
    try:
        file_response = download_file(
            path=minio_path,
        )
        if file_response:
            return file_response
        else:
            return Response(status_code=404)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(InternalServerError(error=str(e)))
