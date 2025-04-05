from typing import Optional
from email import utils
from fastapi import (
    APIRouter, 
    Depends, 
    # Request, 
    BackgroundTasks, 
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
    DataContratResponse,
    ContractManagementResponse,
    TalentAttendanceResponse,
    TalentTimesheetResponse,
    TalentPayrollResponse,

)
from schemas.performance import (
    EditPerformanceRequest,
)
# from core.file import generate_link_download
from repository import talent_monitor as TalentRepo
from repository import performance as PerformanceRepo
from datetime import date, datetime

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
            user=user,
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
    
@router.get("/talent-mapping/{talent_id}",
    responses={
        "200": {"model": TalentMappingResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def talent_mapping_route(
    talent_id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_data = await TalentRepo.data_talent_mapping(
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
    
@router.get("/contract/{talent_id}",
    responses={
        "200": {"model": ContractManagementResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def contract_management_route( 
    talent_id:str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        user_data = await TalentRepo.get_contract_management(
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

@router.get("/attendance/{talent_id}",
    responses={
        "200": {"model": TalentAttendanceResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def talent_attendance_route(
    talent_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        attendance_data = await TalentRepo.get_talent_attendance(
            db=db,
            user_id=talent_id,
            start_date=start_date,
            end_date=end_date
        )
        return common_response(Ok(
            data=attendance_data,
            message="Success get attendance data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/timesheet/{talent_id}",
    responses={
        "200": {"model": TalentTimesheetResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def talent_timesheet_route(
    talent_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        attendance_data = await TalentRepo.get_talent_timesheet(
            db=db,
            user_id=talent_id,
            start_date=start_date,
            end_date=end_date
        )
        return common_response(Ok(
            data=attendance_data,
            message="Success get attendance data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))
    
@router.get("/performance/{talent_id}",
    responses={
        "200": {"model": TalentTimesheetResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def talent_performance_route(
    talent_id: str,
    background_tasks: BackgroundTasks,
    # start_date: Optional[str] = None,
    # end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # if start_date:
        #     start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        # if end_date:
        #     end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        performance_data = await TalentRepo.get_talent_performance(
            db=db,
            user_id=talent_id,
            background_tasks=background_tasks,
            # start_date=start_date,
            # end_date=end_date
        )
        return common_response(Ok(
            data=performance_data,
            message="Success get attendance data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.get("/payroll/{talent_id}",
    responses={
        "200": {"model": TalentPayrollResponse},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def talent_payroll_route(
    talent_id: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # if start_date:
        #     start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        # if end_date:
        #     end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        payroll_data = await TalentRepo.get_talent_payroll()
        return common_response(Ok(
            data=payroll_data,
            message="Success get payroll data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))

@router.put("/performance/{performance_id}",
    responses={
        "201": {"model": CudResponschema},
        "400": {"model": BadRequestResponse},
        "500": {"model": InternalServerErrorResponse},
    },
)
async def edit_performance_route(
    performance_id: str,
    payload: EditPerformanceRequest,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # if start_date:
        #     start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        # if end_date:
        #     end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        user = get_user_from_jwt_token(db, token)
        if not user:
            return common_response(Unauthorized())
        payroll_data = await PerformanceRepo.edit_performance(
            db=db,
            performance_id=performance_id,
            data=payload,
            user=user
        )
        return common_response(Ok(
            data=payroll_data,
            message="Success get payroll data"
            )
        )
    except Exception as e:
        return common_response(BadRequest(message=str(e)))


