from email import utils
from http.client import HTTPException

import httpx
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
    CudResponschema,
)
from schemas.auth import (
    LoginSuccessResponse,
    PermissionsResponse,
    LoginRequest,
    CreateUserRequest,
    MeSuccessResponse,
    RegisRequest,
    FirstLoginUserRequest,
    MenuResponse,
)
# from core.file import generate_link_download
from repository import auth as authRepo

router = APIRouter(tags=["Auth"])
    
@router.post("/first-login",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def first_login_user(
    payload: FirstLoginUserRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized(message="Invalid/Expired token"))
        if user.email != payload.email:
            return common_response(BadRequest(message="Invalid email"))
        data = await authRepo.first_login(
            db=db,
            user=user,
            payload=payload,
        )
        return CudResponse(message="Success change password")
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
@router.post(
    "/regis-face",
        responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def regis_face_route(
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized(message="Invalid/Expired token"))
        data = await authRepo.regis_face(
            db=db,
            user=user,
            upload_file_request=file,
        )
        if not data:
            raise ValueError('Your picture are not valid')
        return CudResponse(message="Picture verified")
    except Exception as e:
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
async def face_route(
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
        "201": {"model": LoginSuccessResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def login(
    request: LoginRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        is_valid, status = await authRepo.check_user_password(db, request.email, request.password)
        if not is_valid:
            return common_response(BadRequest(message="Invalid Credentials"))

        # ========= BEGIN PENGECEKAN STATUS USER
        if is_valid and is_valid.isact != True:
            return common_response(BadRequest(message="Pengguna Tidak Aktif"))
        # ========= END PENGECEKAN STATUS USER

        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        await authRepo.create_user_session(db=db, user_id=user.id, token=token)

        # Extract username and password from the request
        username = request.email
        password = request.password

        # Make an external request to the given URL
        url = "https://face.anaratech.com/auth/token"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": "",
            "client_id": "string",
            "client_secret": "string",
        }
        if status:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, data=data)

            # Check if the external request was successful
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            data_face =  response.json()

        # Return the response from the external service
        face_id_token = data_face["access_token"] if status else None
        return common_response(
                CudResponse(
                    data={
                        "id": str(user.id),
                        "email": user.email,
                        "name": user.name,
                        "isact": user.isact,
                        "role": None if not user.roles else{
                            "nama": user.roles[0].name,
                            "id": user.roles[0].id
                        },
                        "token": token,
                        "token_face_id": face_id_token,
                        "change_password": not status
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
                    },
                    "address":user.address
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
        is_valid, status = await authRepo.check_user_password(
            db, form_data.username, form_data.password
        )
        if not is_valid:
            print("Invalid Credentials")
            return common_response(BadRequest(message="Invalid Credentials"))
        user = is_valid
        token = await generate_jwt_token_from_user(user=user)
        await authRepo.create_user_session(db=db, user_id=user.id, token=token)
        return {"access_token": token, "token_type": "Bearer"}
    except Exception as e:
        print("Error : \n",e)
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
    
@router.get(
    "/menu",
    responses={
        "200": {"model": MenuResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def menu(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())

        list_menu = authRepo.generate_menu_tree_for_user(db=db, user=user)

        return common_response(Ok(data={"results": list_menu}))
    except Exception as e:
        import traceback

        traceback.print_exc()
        return common_response(BadRequest(message=str(e)))