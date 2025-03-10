from email import utils
from fastapi import APIRouter, Depends, Request, BackgroundTasks, Request, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError
from models import get_db
from core.file import generate_link_download
from models.User import User
from core.security import (
    generate_hash_password,
    get_user_permissions,
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
from schemas.auth import (
    LoginSuccessResponse,
    PermissionsResponse,
    LoginRequest,
    CreateUserRequest,
    MeSuccessResponse,
    RegisRequest
)
# from core.file import generate_link_download
from repository import auth as authRepo

router = APIRouter(tags=["Auth"])


@router.post("/create-user",
    responses={
        "200": {"model": CudResponses},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def create_ser(
    payload: CreateUserRequest,
    db: AsyncSession = Depends(get_db)
):  # <-- Perbaikan di sini
    try:
        new_user = User(
            email=payload.email,
            name=payload.name,
            phone=payload.phone,
            face_id=payload.face_id,
            password=generate_hash_password("0000")
        )
        db.add(new_user)
        try:
            db.commit()
            db.refresh(new_user)  # <-- Pastikan data tersimpan sebelum digunakan
            return common_response(CudResponse(message="User added!", data={"user_id": str(new_user.id)}))
        except IntegrityError as e:
            print("ini e: \n", e.orig)
            error_message = str(e.orig)
            if "duplicate key value" in error_message:
                if 'email' in error_message:
                    raise ValueError("Email sudah terdaftar. Silakan gunakan email lain.")
                elif 'phone' in error_message:
                    raise ValueError("Nomor telepon sudah terdaftar. Silakan gunakan nomor lain.")
                else:
                    raise ValueError("Data duplikat terdeteksi.")
            else: 
                raise
    except Exception as e:
        db.rollback()  # <-- Hindari data corrupt jika error terjadi
        return common_response(BadRequest(message=str(e)))
@router.post(
    "/face",
        responses={
        "201": {"model": MeSuccessResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def face(
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized(message="Invalid/Expired token"))
        data = await authRepo.face(
            db=db,
            user=user,
            upload_file=file,
        )
        if not data:
            raise ValueError('Face not verified')
        return CudResponse(message="Verified")
    except Exception as e:
        import traceback
        print("ERROR :",e)
        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))

@router.post(
    "/login",
    responses={
        "200": {"model": LoginSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def login(
    request: LoginRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        is_valid = await authRepo.check_user_password(db, request.email, request.password)
        if not is_valid:
            return common_response(BadRequest(message="Invalid Credentials"))

        # ========= BEGIN PENGECEKAN STATUS USER
        if is_valid and is_valid.is_active != True:
            return common_response(BadRequest(message="Pengguna Tidak Aktif"))
        # ========= END PENGECEKAN STATUS USER

        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        await authRepo.create_user_session(db=db, user_id=user.id, token=token)

        return common_response(
            Ok(
                data={
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "is_active": user.is_active,
                    "role": None if not user.roles else{
                        "nama": user.roles[0].name_role,
                        "id": user.roles[0].id
                    },
                    "wilayah": None if user.wilayah is None else{
                        "nama": user.wilayah.name_wilayah,
                        "id": user.wilayah.id
                    },
                    "token": token
                },
                message="Login Success"
            )
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))


@router.get(
    "/me",
    responses={
        "200": {"model": MeSuccessResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def me(
        request: Request,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
        ):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        old_token = token
        refresh_token = await generate_jwt_token_from_user(user=user)
        # turn on for mobile 
        await authRepo.create_user_session_me(db=db, user_id=user.id, token=token, old_token=old_token)
        return common_response(
            Ok(
                data={
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name,
                    "isact": user.isact,
                    "phone": user.phone,
                    "refreshed_token": refresh_token,
                    "image": generate_link_download(user.face_id),
                    "role": {
                        "id": user.roles[0].id if user.roles else None,
                        "name": user.roles[0].name if user.roles else None,
                    }
                }
            )
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))


@router.post("/token")
async def generate_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    try:
        is_valid = await authRepo.check_user_password(
            db, form_data.username, form_data.password
        )
        if not is_valid:
            return common_response(BadRequest(error="Invalid Credentials"))
        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        await authRepo.create_user_session(db=db, user_id=user.id, token=token)
        return {"access_token": token, "token_type": "Bearer"}
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get(
    "/permissions",
    responses={
        "200": {"model": PermissionsResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def permissions(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_permissions = get_user_permissions(db=db, user=user)

        return common_response(
            Ok(
                data={
                    "results": [
                        {
                            "id": x.id,
                            "permission": x.name,
                            "module": {
                                "id": x.module.id,
                                "nama": x.module.name,
                            }
                            if x.module != None
                            else None,
                        }
                        for x in user_permissions
                    ]
                },
                message="Success get permisson"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))