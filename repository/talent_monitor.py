from typing import Optional, List
import secrets
from math import ceil
from sqlalchemy import or_, select, func
from sqlalchemy.orm import Session, aliased, joinedload
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local, generate_link_download
from models.User import User
from models.Role import Role
from models.Client import Client
from models.Contract import Contract
from models.ClientOutlet import ClientOutlet
from models.ShiftSchedule import ShiftSchedule
from models.UserRole import UserRole
from models.Attendance import Attendance
from models.LeaveTable import LeaveTable
from models.TimeSheet import TimeSheet
from datetime import datetime, timedelta, date
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.talent_monitor import (
    ListAllUser,
    TalentInformation,
    Organization,
    TalentMapping,
    DataWorkingArrangement,
    DataOutlet,
    ContractManagement,
    DataContractManagement,
    HistoryContract,
    ClientData,
    TalentAttendance,
    LeaveSubmission,
    AttendanceGraphData,
    AttendanceData,
    TalentTimesheet,
    TimeSheetHistory,
    PerformanceHistory,
    TalentPerformance,
    ListTalentPayroll,
    TalentPayroll,
)
import os
import asyncio
from repository.performance import add_performance

async def approve_leave(
    db: Session,
    leave_id: str,
    user: User,
    status: Optional[int] = 2,  # 3: Rejected, 2: Approved
) -> bool:
    """
    Approve or reject a leave request based on the provided status.
    """
    try:
        leave = db.execute(
            select(LeaveTable).where(LeaveTable.id == leave_id, LeaveTable.isact == True)
        ).scalar()
        
        if not leave:
            raise ValueError("Leave request not found")

        # Update the status of the leave request
        leave.status = status
        leave.updated_at = datetime.now(timezone(TZ))
        leave.updated_by = user.id_user
        db.add(leave)
        db.commit()
        return True
    except ValueError as ve:
        raise ve
    except Exception as e:
        print("Error approving leave: ", e)
        raise ValueError("Failed to approve leave")

async def reject_leave(
    db: Session,
    leave_id: str,
    user: User,
    status: Optional[int] = 3,  # 3: Rejected, 2: Approved
) -> bool:
    """
    Approve or reject a leave request based on the provided status.
    """
    try:
        leave = db.execute(
            select(LeaveTable).where(LeaveTable.id == leave_id, LeaveTable.isact == True)
        ).scalar()
        
        if not leave:
            raise ValueError("Leave request not found")

        # Update the status of the leave request
        leave.status = status
        leave.updated_at = datetime.now(timezone(TZ))
        leave.updated_by = user.id_user
        db.add(leave)
        db.commit()
        return True
    except ValueError as ve:
        raise ve
    except Exception as e:
        print("Error approving leave: ", e)
        raise ValueError("Failed to approve leave")

async def get_talent_payroll() -> TalentPayroll:
    """
    Return payroll data using the TalentPayroll Pydantic model.
    """
    try:
        # Get the current date and time in the specified timezone
        now = datetime.now(timezone(TZ))
        month = now.strftime("%m")
        year = now.strftime("%Y")
        
        # Create a unique filename for the payroll file
        filename = f"payroll_{secrets.token_hex(4)}_{month}_{year}.xlsx"
        
        # Define the local path for saving the payroll file
        local_path = os.path.join(LOCAL_PATH, "payroll", filename)
        
        # Generate the download link for the payroll file
        download_link = generate_link_download(local_path)
        
        # Return the TalentPayroll model
        return TalentPayroll(
            emp_name=None,  # Placeholder, update if employee name is available
            emp_code=None,  # Placeholder, update if employee code is available
            emp_role=None,  # Placeholder, update if employee role is available
            payroll=[
                ListTalentPayroll(
                    month=f"{month}-{year}",
                    gaji_pokok=0.00,
                    tunjangan_makan=0.00,
                    bpjs_kesehatan=0.00,
                    pajak_pph21=0.00,
                    bonus=0.00,
                    agency_fee=0.00,
                    total=0.00
                )
            ]
        ).model_dump()
    except Exception as e:
        print("Error get talent payroll: \n", e)
        raise ValueError("Failed to get talent payroll")

async def get_talent_performance(
    db:Session,
    user_id:str,
    request_user:User,
    background_tasks: Optional[any] = None,
)->TalentPerformance:
    try:
        # Fetch user details
        user_query = db.execute(select(User).where(User.id_user == user_id))
        user = user_query.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        ls_performance = []
        for item in user.performance_user:
            current_month = datetime.now().month
            current_year = datetime.now().year
            isedit = True if item.date and item.date.month == current_month and item.date.year == current_year else False
            isedit = isedit if request_user.roles[0].id == 2 else False
            ls_performance.append(PerformanceHistory(
                id=item.id,
                date=item.date.strftime("%A, %d %B %Y") if item.date else None,
                softskill=item.softskill,
                hardskill=item.hardskill,
                total_point=f"{item.softskill+item.hardskill}/10 ",
                notes=item.notes,
                isedit=isedit,
             ))
        
        # Determine performance level based on current month's total points
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Find most recent performance record for current month
        current_month_performance = next(
            (p for p in user.performance_user if p.date and 
             p.date.month == current_month and 
             p.date.year == current_year),
            None
        )
        
        performance_level = "Not Available"
        if current_month_performance:
            total_point = current_month_performance.softskill + current_month_performance.hardskill
            if total_point > 8:
                performance_level = "Excellent"
            elif total_point > 5:
                performance_level = "Meet Expectations"
            else:
                performance_level = "Needs Improvement"
        # background_tasks.add_task(
        #     add_performance,
        #     emp_id=user.id,
        # )
        return TalentPerformance(
            name=user.name,
            role_name=user.roles[0].name if user.roles else None,
            performance=performance_level,
            history=ls_performance
        ).dict()
    except Exception as e:
        print("Error get talent performance: \n",e)
        raise ValueError("Failed get talent performance")

async def get_talent_timesheet(
    db: Session,
    user_id: str,
    start_date: date = None,
    end_date: date = None
) -> TalentTimesheet:
    try:
        # Set default date range if not provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # Fetch user details
        user_query = db.execute(select(User).where(User.id_user == user_id))
        user = user_query.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Fetch timesheet records with database-level filtering
        timesheet_query = db.execute(
            select(TimeSheet)
            .where(
                TimeSheet.emp_id == user.id,
                TimeSheet.isact == True,
                TimeSheet.clock_out >= start_date,
                TimeSheet.clock_out <= end_date
            )
            .limit(100)
        )
        grouped_attendance_query = db.execute(
            select(
                Attendance.date,
            )
            .where(
                Attendance.emp_id == user.id,
                Attendance.isact == True,
                Attendance.date >= start_date,
                Attendance.date <= end_date
            )
            .group_by(Attendance.date)
            .limit(100)
        )

        # Fetch all attendance records grouped by date
        grouped_attendance_results = grouped_attendance_query.fetchall()
        
        # Calculate total attendance count across all days
        total_attendance_count = sum(1 if result.date else 0 for result in grouped_attendance_results) if grouped_attendance_results else 0
        
        # For debugging
        print("grouped_attendance results: \n", total_attendance_count)

        filtered_timesheet = timesheet_query.scalars().all()

        timesheet = []
        # Format timesheet data
        for history in filtered_timesheet:
            timesheet.append(TimeSheetHistory(
                date=history.created_at.date().strftime("%A, %d %B %Y") if history.created_at else None,
                working_hours=history.total_hours.strftime("%H:%M") if history.total_hours else None,
                notes=history.note,
                outlet=Organization(
                    id=history.outlets.id if history.outlets else 0,
                    name=history.outlets.name if history.outlets else None
                    )
                )
            )

        return TalentTimesheet(
            name=user.name,
            role_name=user.roles[0].name if user.roles else None,
            total_workdays=total_attendance_count,  
            timesheet=timesheet
        ).dict()
    except Exception as e:
        print("Error get talent timesheet: \n", e)
        raise ValueError("Failed get talent timesheet")

async def get_talent_attendance(
    db: Session, 
    user_id: str, 
    user:User,
    start_date: date = None, 
    end_date: date = None
) -> TalentAttendance:
    try:
        # Set default date range (last 30 days)
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # Fetch user details
        user_query = db.execute(select(User).where(User.id_user == user_id))
        user = user_query.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Fetch attendance data with pagination
        attendance_query = db.execute(
            select(Attendance)
            .where(
                Attendance.emp_id == user.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date,
                Attendance.isact == True
            )
            .limit(100)  # Limit to 100 records per query
        )
        attendance_records = attendance_query.scalars().all()
        attendance_data = [
            AttendanceData(
                total_workdays=len(attendance_records),  # Count of attendance records
                id=record.id,
                date=record.date.strftime("%A, %d %B %Y") if record.date else None,
                location=record.outlets.name if record.outlets  else None,  # Add location if available
                clock_in=record.clock_in.strftime("%H:%M") if record.clock_in else None,
                clock_out=record.clock_out.strftime("%H:%M") if record.clock_out else None,
            )
            for record in attendance_records
        ]

        # Fetch leave submissions with pagination
        leave_query = db.execute(
            select(LeaveTable)
            .where(
                LeaveTable.emp_id == user.id,
                LeaveTable.start_date >= start_date,
                LeaveTable.end_date <= end_date,
                LeaveTable.isact == True
            )
            .limit(100)  # Limit to 100 records per query
        )
        leave_records = leave_query.scalars().all()
        leave_submissions = [
            LeaveSubmission(
                leave_id=record.id,
                total_pending=0,  # Placeholder, calculate if needed
                type=record.type,
                date_period=(record.end_date - record.start_date).days if record.start_date and record.end_date else 0,
                start_date=record.start_date.strftime("%d %B %Y") if record.start_date else None,
                end_date=record.end_date.strftime("%d %B %Y") if record.end_date else None,
                note=record.note,
                evidence=record.evidence,
                file_name=None,  # Add file name if available
                status=Organization(
                    id=record.status_leave.id if record.status_leave and record.status_leave else 0,
                    name=record.status_leave.name if record.status_leave and record.status_leave else None
                ),
                isedit=True if record.status_leave.id == 1 and user.roles[0].id == 2 else False
            )
            for record in leave_records
        ]

        # Calculate attendance graph data based on status
        graph_query = db.execute(
            select(
                Attendance.status,
                func.count(Attendance.id).label("count")
            )
            .where(
                Attendance.emp_id == user.id,
                Attendance.date >= start_date,
                Attendance.date <= end_date,
                Attendance.isact == True
            )
            .group_by(Attendance.status)
        )
        graph_results = graph_query.all()
        graph_data = [
            AttendanceGraphData(type=result.status, desktop=result.count)
            for result in graph_results
        ]

        # Construct TalentAttendance response
        return TalentAttendance(
            name=user.name,
            role=Organization(
                id=user.roles[0].id if user.roles and user.roles[0] else 0,
                name=user.roles[0].name if user.roles and user.roles[0] else None
            ),
            attendance=attendance_data,
            leave_submission=leave_submissions,
            graph=graph_data,
        ).dict()
    except Exception as e:
        # Log error to centralized logging system
        print(f"Error getting talent attendance: {e}")
        raise ValueError("Failed to get talent attendance data")

async def data_talent_mapping(
    db: Session,
    talent_id: str,
) -> TalentMapping:
    """
    Get talent mapping data by talent_id including client and outlet information
    """
    try:
        # Get user with optional client and outlet relationship
        query = select(
            User, 
            Client, 
            ClientOutlet
        ).outerjoin(
            Client, User.client_id == Client.id
        ).outerjoin(
            ClientOutlet, User.outlet_id == ClientOutlet.id
        ).filter(
            User.id_user == talent_id,
            User.isact == True
        ).limit(1)
        
        result = db.execute(query).first()
        
        if not result:
            raise ValueError("Talent not found")
        
        user, client, outlet = result
        
        # Get shift information
        shift_query = select(ShiftSchedule).filter(
            ShiftSchedule.emp_id == user.id,
            ShiftSchedule.isact == True
        )
        shifts = db.execute(shift_query).scalars().all()
        
        # Format shift data according to DataWorkingArrangement model
        work_arrangements = []
        for shift in shifts:
            work_arr = DataWorkingArrangement(
                shift_id=shift.id_shift or "S001",
                day=shift.day or "Monday",
                time_start=shift.time_start.strftime("%H:%M") if shift.time_start else "08:00",
                time_end=shift.time_end.strftime("%H:%M") if shift.time_end else "15:00"
            )
            work_arrangements.append(work_arr)
        
        # If no shifts found, add a default one to match model requirements
        # if not work_arrangements:
        #     work_arrangements.append(DataWorkingArrangement())
        
        # Create output using the proper pydantic models
        client_org = ClientData(
            id=client.id_client if client else None,
            name=client.name if client else None,
            address=client.address if client else None
        ) if client else None
        
        outlet_data = DataOutlet(
            name=outlet.name if outlet else None,
            address=outlet.address if outlet else None,
            latitude=float(outlet.latitude) if outlet and outlet.latitude else None,
            longitude=float(outlet.longitude) if outlet and outlet.longitude else None
        ) if outlet else None
        
        return TalentMapping(
            client=client_org,
            outlet=outlet_data,
            workdays=len(work_arrangements) if work_arrangements else 0,
            workarr=work_arrangements if work_arrangements != [] else None
        ).dict()
        
    except Exception as e:
        print(f"Error getting talent mapping: {e}")
        raise ValueError(f"Failed to get talent mapping")

async def data_talent_information(
    db:Session,
    talent_id:str,
)->TalentInformation:
    try:
        query = select(User).filter(User.id_user == talent_id).limit(1)
        data = db.execute(query).scalar_one_or_none()
        
        if not data:
            raise ValueError("User not found")
    
        return await formating_talent_information(data)
    except Exception as e:
        print("Error data talent info: \n",e)
        raise ValueError("Failed get data detail informatoin")

async def formating_talent_information(d:User) -> TalentInformation:
    role = Organization(
        id=d.roles[0].id if d.roles and d.roles[0] else 0,
        name=d.roles[0].name if d.roles and d.roles[0] else ""
    )
    
    return TalentInformation(
        name=d.name,
        role=role,
        talent_id=d.id_user,
        dob=d.birth_date.strftime("%d-%m-%Y") if d.birth_date else None,
        phone=d.phone,
        address=d.address,
        nik=d.nik if d.nik else "",
        email=d.email,
        photo=generate_link_download(d.photo) if d.photo else None
    ).dict()

async def list_talent(
    db: Session,
    page: int,
    page_size: int,
    src: Optional[str] = None,
    user:Optional[User] = None,
)->ListAllUser:
    try:
        limit = page_size
        offset = (page - 1) * limit

        # Query utama dengan JOIN ke Client
        query = (select(
            User.id_user,
            User.name,
            User.birth_date,
            User.nik,
            User.email,
            User.phone,
            User.address,
            User.isact,
            User.photo,
            )
            .join(UserRole, User.id == UserRole.c.emp_id)
            .filter(User.isact == True, UserRole.c.role_id == 1)
            )

        # Query count untuk paginasi
        query_count = (
            select(func.count(User.id))
            .join(UserRole, User.id == UserRole.c.emp_id)
            .filter(User.isact == True, UserRole.c.role_id == 1)
            )
        
        # If user == admin, hanya client dia
        print("user: ", user.roles[0].id if user else None)
        if user:
            if user.roles[0].id==2:
                query = query.filter(or_(User.client_id == user.client_id))
                query_count = query_count.filter(or_(User.client_id == user.client_id))

        # Jika ada pencarian (src), cari di nama user & nama client
        if src:
            query = (query.filter(
                (User.name.ilike(f"%{src}%")) |
                (User.email.ilike(f"%{src}%")) |
                (User.phone.ilike(f"%{src}%")) |
                (User.address.ilike(f"%{src}%")) |
                (User.nik == src) 
            ))

            query_count = (query_count.filter(
                (User.name.ilike(f"%{src}%")) |
                (User.email.ilike(f"%{src}%")) |
                (User.phone.ilike(f"%{src}%")) |
                (User.address.ilike(f"%{src}%")) |
                (User.nik == src)
            ))

        # Tambahkan order, limit, dan offset
        query = (query.order_by(User.created_at.desc())
                 .limit(limit)
                 .offset(offset))

        # Eksekusi query
        data = db.execute(query).all()
        num_data = db.execute(query_count).scalar()
        num_page = ceil(num_data / limit)

        return (await formating_talent(data), num_data, num_page)

    except Exception as e:
        raise ValueError(e)
    
async def formating_talent(data:List[User]):
    ls_data = []
    for d in data:
        ls_data.append({
            "talend_id": d.id_user,
            "name": d.name,
            "dob": d.birth_date.strftime("%d-%m-%Y") if d.birth_date else None,
            "nik": d.nik,
            "email": d.email,
            "phone": d.phone,
            "address": d.address,
            "photo": generate_link_download(d.photo) if d.photo else None,
        })
    return ls_data

async def get_contract_management(db: Session, talent_id: str) -> ContractManagement:
    """
    Get contract management data for a specific talent_id.
    """
    try:
        user = db.execute(
            select(User)
            .options(
                joinedload(User.roles),
                joinedload(User.contract_user)
            )
            .filter(User.id_user == talent_id, User.isact == True)
        ).unique().scalar_one_or_none()

        if not user:
            raise ValueError("Talent not found")

        # Extract role name
        role_name = user.roles[0].name if user.roles else None

        # Extract active contract (most recent)
        active_contract = None
        if user.contract_user:
            active_contract = max(
                user.contract_user,
                key=lambda c: c.created_at,
                default=None
            )

        # Format active contract data
        active_contract_data = DataContractManagement(
            id=active_contract.id,
            start_date=active_contract.start.strftime("%d-%m-%Y") if active_contract and active_contract.start else None,
            end_date=active_contract.end.strftime("%d-%m-%Y") if active_contract and active_contract.end else None,
            file=generate_link_download(active_contract.file) if active_contract and active_contract.file else None
        ) if active_contract else None

        # Format contract history
        history_data = [
            HistoryContract(
                start_date=contract.start.strftime("%d-%m-%Y") if contract.start else None,
                end_date=contract.end.strftime("%d-%m-%Y") if contract.end else None,
                file=generate_link_download(contract.file) if contract.file else None,
                file_name=contract.file_name
            )
            for contract in sorted(user.contract_user, key=lambda c: c.created_at, reverse=True)
        ]

        # Return ContractManagement model
        return ContractManagement(
            talent_id=user.id_user,
            talent_name=user.name,
            talent_role=role_name,
            contract=active_contract_data,
            history=history_data
        ).dict()
    except Exception as e:
        print(f"Error getting contract management: {e}")
        raise ValueError("Failed to get contract management data")