from http.client import HTTPException
import httpx
from fastapi import APIRouter, Depends, File, Response, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models import get_db
from core.mail import send_reset_password_email
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
from core.myredis import get_data_with_cache
from datetime import datetime
from core.security import get_user_from_jwt_token, oauth2_scheme, generate_jwt_token_from_user
from schemas.common import NoContentResponse, InternalServerErrorResponse, UnauthorizedResponse, BadRequestResponse, CudResponschema
from repository import mobile as mobileRepo
from repository import shift as shiftRepo
from repository import auth as authRepo
from repository import izin as izinRepo
from repository import timesheet as timesheetRepo
from schemas.mobile import *
from schemas.shift import *
from schemas.auth import (
    FirstLoginUserRequest,
    LoginRequest,
    LoginSuccessResponse,
    ForgotPasswordSendEmailResponse,
    ForgotPasswordSendEmailRequest,
    ForgotPasswordChangePasswordRequest,
    ForgotPasswordChangePasswordResponse,
)
from schemas.izin import DataIzinResponse
from settings import MINIO_BUCKET
import os

router = APIRouter(tags=["Mobile"])


@router.post(
    "/forgot-password/send-email",
    responses={
        "200": {"model": ForgotPasswordSendEmailResponse},
        "400": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def request_forgot_password_send_email(
    request: ForgotPasswordSendEmailRequest,
    db: Session = Depends(get_db)
    # token: str = Depends(oauth2_scheme)
):
    try:
        user, status = await authRepo.get_user_by_email(db=db, email=request.email)
        if user == None:
            return common_response(BadRequest(message='user not found'))

        token = await authRepo.generate_token_forgot_password(db=db, user=user)
        await send_reset_password_email(
            email_to=user.email, 
            body={
                "email": user.email,
                "token": token,
            })
        return common_response(
            Ok(
                message="success kirim email ganti password, silahkan cek email anda"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))


@router.post(
    "/forgot-password/change-password",
    responses={
        "200": {"model": ForgotPasswordChangePasswordResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def request_forgot_password_change_password(
    request: ForgotPasswordChangePasswordRequest,
    db: Session = Depends(get_db)
):
    try:
        user = await authRepo.change_user_password_by_token(
            db=db, token=request.token, new_password=request.password
        )
        if user == None:
            return common_response(BadRequest(message="User Not Found"))
        elif user == False:
            return common_response(Unauthorized(message="Invalid/Expired Token for Change Password"))

        return common_response(Ok(message="success menganti password anda"))
    except Exception as e:
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
    db: Session = Depends(get_db)
):
    try:
        is_valid, status = await authRepo.check_user_password_mobile(db, request.email, request.password)
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

@router.post("/first-login",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def first_login_user(
    payload: FirstLoginUserRequest,
    db: Session = Depends(get_db),
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
        return common_response(CudResponse(message="Success change password"))
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
        return common_response(CudResponse(message="Picture verified"))
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

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
    
@router.get("/status-checkin",
    responses={
        "200": {"model": CheckAttendanceResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def status_checkin(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    """
    Endpoint for status employee check-in.
    """
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data = await mobileRepo.get_status_attendance(db, user)
        return common_response(Ok(
            message="Success get data",
            data=data
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
    background_tasks: BackgroundTasks,
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
        await mobileRepo.add_checkout(
            db=db, 
            data=data, 
            user=user, 
            background_tasks=background_tasks
        )
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
async def list_absensi_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    start:Optional[str] = None,
    end:Optional[str] = None,
    order: Optional[str] = "asc",
    src: Optional[str] = None,    
):
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        # data_shift = await get_data_with_cache(
        #     key=f"absensi-{user.id}-{start}-{end}-{order}",
        #     fetch_function=mobileRepo.get_menu_absensi,
        #     model=DataMenuAbsensi,
        #     db=db, 
        #     user=user,
        #     src=src, 
        #     start=start, 
        #     end=end, 
        #     order=order
        # )
        data_shift = await mobileRepo.get_menu_absensi(db, user,src, start, end, order)
        return common_response(Ok(
            message="Success Data Menu Absensi",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/master/izin",
    responses={
        "200": {"model": DataIzinResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def list_izin_option_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    src:Optional[str] = None,
):
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await izinRepo.get_izin_option(db, user, src)
        return common_response(Ok(
            message="Success Data Menu Absensi",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.get("/menu-timesheet",
    responses={
        "200": {"model": DataIzinResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def data_menu_timesheet_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    bulan:Optional[str] = None,
):
    '''
    kolom bulan bisa diisi dengan date hari pertama bulan terpilih 'yyyy-mm-dd'
    contoh: 2025-08-01 untuk bulan agustus 2025
    '''
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await timesheetRepo.get_data_menu_timesheet(db, user, bulan)
        return common_response(Ok(
            message="Success Data Menu Absensi",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/today-detail",
    responses={
        "200": {"model": DetailTimesheetResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def detail_menu_timesheet_route(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    '''
    semangat bang
    '''
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await timesheetRepo.get_detail_timesheet_today(db, user)
        return common_response(Ok(
            message="Success Data Menu Absensi",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.get("/menu-timesheet/{id_timesheet}",
    responses={
        "200": {"model": DetailTimesheetResponse},
        "400": {"model": BadRequestResponse},
        "401": {"model": UnauthorizedResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def detail_menu_timesheet_route(
    id_timesheet:int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    '''
    id_timesheet disi dengan id yang ada di list
    '''
    user = get_user_from_jwt_token(db, token)
    if not user:
        return Unauthorized()
    try:
        data_shift = await timesheetRepo.get_detail_timesheet(db, user, id_timesheet)
        return common_response(Ok(
            message="Success Data Menu Absensi",
            data=data_shift,
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))