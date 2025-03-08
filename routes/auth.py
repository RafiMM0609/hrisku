from email import utils
from fastapi import APIRouter, Depends, Request, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError
from core.security import (
    generate_hash_password,
    get_user_permissions,
    get_user_from_jwt_token,
)
from models import get_db
from models.User import User
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
    CudResponse,
)
from schemas.auth import (
    LoginSuccessResponse,
    PermissionsResponse,
    LoginRequest,
    CreateUserRequest,
    MeSuccessResponse,
)
# from core.file import generate_link_download
from repository import auth as authRepo

router = APIRouter(tags=["Auth"])


@router.post("/create-user",
    responses={
        "200": {"model": CudResponse},
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
            password=generate_hash_password("0000")
        )
        db.add(new_user)
        try:
            db.commit()
            db.refresh(new_user)  # <-- Pastikan data tersimpan sebelum digunakan
            return {"message": "User added!", "user_id": new_user.id}
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
        return common_response(BadRequest(error=str(e)))

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
                }
            )
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return common_response(BadRequest(error=str(e)))


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
        request: Request ,
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
        ):
    try:
        old_token = token
        user = request.state.user
        db = request.state.db
        ls_unitkerja = []
        ls_cabang = []
        wilayah = None
        zona = None
        for data in user.unit_kerja:
            ls_unitkerja.append(
                {
                "id": data.id if data else None,
                "nama": data.name_unit_kerja if data else None
                }    
            )
            ls_cabang.append(
                {
                "id": data.cabang.id if data.cabang else None,
                "nama":data.cabang.name_cabang if data.cabang else None
                }
            )
            wilayah = {
                "id": data.cabang.wilayah.id,
                "nama": data.cabang.wilayah.name_wilayah
            } if data.cabang.wilayah else None
            zona = {
                "id": data.cabang.wilayah.zonas[0].id if data.cabang.wilayah.zonas else None,
                "name_zona": data.cabang.wilayah.zonas[0].name_zona if data.cabang.wilayah.zonas else None,
            } if data.cabang.wilayah.zonas else None
        if ls_cabang == [] or ls_unitkerja == []:
            ls_cabang, ls_unitkerja = await authRepo.getCabangakaUnit(
                user=user,
                ls_unitkerja=ls_unitkerja,
                ls_cabang=ls_cabang,
            )
        if wilayah is None:
            wilayah_nama = await authRepo.getWilayah(db=db, wilayah_id=user.wilayah_id)
            wilayah = {
                "id": user.wilayah_id,
                "nama": wilayah_nama
            }
        if zona is None and user.wilayah_id is not None:
            zona_name, zona_id = await authRepo.getZona(wilayah_id=user.wilayah_id, db=db)
            zona = {
                "id":zona_id,
                "name_zona": zona_name
            }
        refresh_token = await generate_jwt_token_from_user(user=user)
        # turn on for mobile 
        await authRepo.create_user_session_me(db=db, user_id=user.id, token=token, old_token=old_token)
        return common_response(
            Ok(
                data={
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "name": user.name,
                    "is_active": user.is_active,
                    "phone": user.phone,
                    "refreshed_token": refresh_token,
                    "image": generate_link_download(user.photo_user),
                    "role": {
                        "id": user.roles[0].id if user.roles else None,
                        "nama": user.roles[0].name_role if user.roles else None,
                    },
                    "unit_kerja": [
                        {
                            "id": data['id'],
                            "nama": data['nama']
                        } for data in ls_unitkerja
                    ],
                    "cabang": [
                        {
                            "id": data['id'],
                            "nama": data['nama']
                        } for data in ls_cabang
                    ],
                    "unit_kerja": [
                        {
                            "id": data['id'],
                            "nama": data['nama']
                        } for data in ls_unitkerja
                    ],
                    "cabang": [
                        {
                            "id": data['id'],
                            "nama": data['nama']
                        } for data in ls_cabang
                    ],
                    "wilayah": {
                        "id": wilayah['id'] if wilayah is not None else None,
                        "nama": wilayah['nama'] if wilayah is not None else None,
                    },
                    "zona" : {
                        "id": zona['id'] if zona is not None else None,
                        "name_zona": zona['name_zona'] if zona is not None else None,
                    },
                    "jenis_kelamin": user.jenis_kelamin,
                    "code_user": user.code_user,
                }
            )
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(error=str(e)))


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
        return common_response(BadRequest(error=str(e)))
    
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
                }
            )
        )
    except Exception as e:
        return common_response(BadRequest(error=str(e)))