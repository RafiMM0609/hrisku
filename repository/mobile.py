import calendar
from typing import Optional, List, Tuple, Type
from math import ceil, radians, sin, cos, sqrt, atan2  # Add these imports for Haversine formula
import secrets
from sqlalchemy import select, func, distinct, or_, and_, case  # Added and_ import
from sqlalchemy.orm import Session, aliased
from models.User import User
from models.Role import Role
from models import SessionLocal
from models.Attendance import Attendance
from models.ShiftSchedule import ShiftSchedule
from models.LeaveTable import LeaveTable
from models.ClientOutlet import ClientOutlet
from models.Client import Client
from models.TimeSheet import TimeSheet
from models.Izin import Izin
from models.Payroll import Payroll
from datetime import datetime, timedelta, time
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.mobile import (
    CheckinRequest,
    CheckoutRequest,
    LeaveRequest,
    DataOutlet,
    DataLeave,
    Organization,
    DataMenuCheckout,
    DataMenuAbsensi,
    HistoryAbsensi_Menuabsensi,
    HeaderAbsensi,
    CheckAttendance,
    DetailDataAbsensi,
    ListPayroll,
    DetailPayroll,
)
from repository.payroll import add_monthly_salary_emp, generate_file_excel
from decimal import Decimal
from core.file import generate_link_download

async def get_list_payroll(
    db:Session,
    user:User,
    background_tasks:any=None,
) -> List[ListPayroll]:
    """
    Return a list of payroll items, validated against the ListPayroll Pydantic model. Always return with model_dump.
    """
    try:
        # Data preparation
        today = datetime.now(timezone(TZ)).date()

        # Query payroll data for the user
        query_payroll = (
            select(Payroll).filter(
                Payroll.client_id == user.client_id,
                Payroll.emp_id == user.id,
                Payroll.isact == True,
                # Payroll.payment_date.between(start_of_month, end_of_month),
            )
            .order_by(Payroll.created_at.desc())
            .limit(3)
        )
        payroll_data = db.execute(query_payroll).scalars().all()

        if not payroll_data:
            # If no payroll data found, return an empty list
            return []
        
        list_payroll = []
        for payroll in payroll_data:
            list_payroll.append(
                ListPayroll(
                    id=payroll.id,
                    date=payroll.payment_date.strftime("%B %Y") if payroll.payment_date else None,
                    performance="You are doing great 10/10",
                    utilization="100%",
                    net_salary=format_to_idr(payroll.net_salary),  # Convert to float
                ).model_dump()
            )
                # Add monthly salary task
        data_monthly_salary = {
            "emp_id": user.id,
            "client_id": user.client_id,
        }
        background_tasks.add_task(
            add_monthly_salary_emp,
            **data_monthly_salary
        )
        background_tasks.add_task(
            generate_file_excel,
            **data_monthly_salary
        )
        return list_payroll
    except Exception as e:
        print("Error get list payroll: \n", e)
        raise ValueError("Failed to get list payroll")
    
def format_to_idr(value):
    return f"Rp {value:,.2f}".replace(',', '.').replace('.', ',', 1)

async def get_detail_payroll(
    db:Session,
    user:User,
    payroll_id:str,
) -> DetailPayroll:
    """
    Return a DetailPayroll object with default values.
    """
    try:
        # Data preparation
        data_payroll = db.query(Payroll).filter(
            Payroll.isact == True,
            Payroll.id == payroll_id,
        ).first()
        data_client = db.query(Client).filter(
            Client.isact == True,
            Client.id == user.client_id,
        ).first()
        data_outlet = db.query(ClientOutlet).filter(
            ClientOutlet.isact == True,
            ClientOutlet.id == user.outlet_id,
        ).first()
        if not data_payroll:
            raise ValueError("Payroll not found")
        detail_payroll = DetailPayroll(
            date=data_payroll.payment_date.strftime("%B %Y") if data_payroll.payment_date else None,
            client_name=data_client.name if data_client else None,
            client_address=data_client.address if data_client else None,
            client_code=data_client.id_client if data_client else None,
            outlet_name=data_outlet.name if data_outlet else None,
            outlet_address=data_outlet.address if data_outlet else None,
            outlet_latitude=data_outlet.latitude if data_outlet else 0.0,
            outlet_longitude=data_outlet.longitude if data_outlet else 0.0,
            download_link=generate_link_download(data_payroll.file) if data_payroll.file else None,
        ).model_dump()
        return detail_payroll
    except Exception as e:
        print("Error get detail payroll: \n", e)
        raise ValueError("Failed to get detail payroll")



async def get_status_attendance(
  db: Session,
  user: User,      
) -> CheckAttendance:
    try:
        today = datetime.now(timezone(TZ)).date()
        now = datetime.now(timezone(TZ))

        # Fetch today's shift schedule for the user
        today_name = now.strftime("%A")  # Get day name like "Monday", "Tuesday", etc.
        shift = db.execute(
            select(ShiftSchedule).filter(
                ShiftSchedule.emp_id == user.id,
                ShiftSchedule.day == today_name,
                ShiftSchedule.isact == True
            ).limit(1)
        ).scalar()

        # Determine if current time is past shift end time
        past_shift_end = False
        if shift and shift.time_end:
            shift_end_time = datetime.combine(today, shift.time_end).replace(tzinfo=timezone(TZ))
            past_shift_end = now > shift_end_time

        # Adjust the filter for clock_out based on shift end time
        attendance_query = select(Attendance).filter(
            Attendance.emp_id == user.id,
            Attendance.isact == True,
            Attendance.date == today,
        )
        if not past_shift_end:
            attendance_query = attendance_query.filter(
                Attendance.clock_out == None,
            )

        data_attendance = db.execute(attendance_query).scalar()

        if not data_attendance:
            return CheckAttendance(
                clock_in=None,
                clock_out=None,
                outlet=Organization(id=None, name=None),
                date=None
            ).dict()

        return CheckAttendance(
            clock_in=data_attendance.clock_in.strftime("%H:%M") if data_attendance.clock_in else None,
            clock_out=data_attendance.clock_out.strftime("%H:%M") if data_attendance.clock_out else None,
            outlet=Organization(
                id=data_attendance.outlets.id if data_attendance.outlets else None,
                name=data_attendance.outlets.name if data_attendance.outlets else None,
            ),
            date=data_attendance.date.strftime("%d %B %Y") if data_attendance.date else None,
        ).dict()
    except Exception as e:
        print("Error get status attendance: \n", e)
        raise ValueError("Failed get status attendance: \n", e)

def get_range_for_a_month(today:Optional[str]=None)->Tuple[datetime.date, datetime.date]:
    # Data preparation
    if not today:
        today = datetime.now(timezone(TZ)).date()
    else:
        today = datetime.strptime(today, "%d-%m-%Y").date()
    
    # get range 1 month
    first_day_of_month = today.replace(day=1)
    _, last_day = calendar.monthrange(today.year, today.month)
    last_day_of_month = today.replace(day=last_day)
    # last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) if first_day_of_month.month < 12 
    #             else first_day_of_month.replace(year=first_day_of_month.year + 1, month=1, day=1)) - timedelta(days=1)
    
    # Override with parameters if provided
    start_date = first_day_of_month
    end_date = last_day_of_month
    return start_date, end_date

async def get_menu_absensi(
    db: Session,
    user: User,
    src: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    order: Optional[str] = "asc",
) -> DataMenuAbsensi:
    try:
        # Data preparation
        today = datetime.now(timezone(TZ)).date()
        
        # get range 1 month
        # first_day_of_month = today.replace(day=1)
        # last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) if first_day_of_month.month < 12 
        #             else first_day_of_month.replace(year=first_day_of_month.year + 1, month=1, day=1)) - timedelta(days=1)
        
        # # Override with parameters if provided
        # start_date = datetime.strptime(start, "%d-%m-%Y").date() if start else first_day_of_month
        # end_date = datetime.strptime(end, "%d-%m-%Y").date() if end else last_day_of_month
        start_date, end_date = get_range_for_a_month()
        
        # Query attendance data with date filter
        query_data_att = (
            select(Attendance).filter(
            Attendance.emp_id == user.id,
            Attendance.isact == True,
            Attendance.date.between(start_date, end_date)
            )
            .join(ClientOutlet, Attendance.loc_id == ClientOutlet.id, isouter=True)
            .group_by(Attendance.date, Attendance.id)  # Group by date and ID to ensure unique entries
        )
        if src:
            query_data_att = query_data_att.filter(
                or_(
                    ClientOutlet.name.ilike(f"%{src}%")
                )
            )
        if order == "asc":
            query_data_att = query_data_att.order_by(Attendance.created_at.asc())
        elif order == "desc":
            query_data_att = query_data_att.order_by(Attendance.created_at.desc())

        data_att = db.execute(
            query_data_att
            .limit(100)
        ).scalars().all()
        
        # Return Default Data
        if not data_att:
            return DataMenuAbsensi(
            this_month=today.strftime("%B %Y"),
            header=HeaderAbsensi(), 
            history=[]
            ).dict()
        
        # Execute query grouped data
        grouped_data = db.execute(
            select(
                Attendance.date,
                func.count().label("total"),
                func.sum(case((Attendance.status == "Hadir", 1), else_=0)).label("hadir"),
                func.sum(case((Attendance.status == "Absen", 1), else_=0)).label("absen"),
                func.sum(case((Attendance.status == "Sakit", 1), else_=0)).label("sakit"),
                func.sum(case((Attendance.status == "Cuti", 1), else_=0)).label("cuti"),
                func.sum(case((Attendance.status == "Izin", 1), else_=0)).label("izin"),
                func.sum(case((Attendance.status == "Terlambat", 1), else_=0)).label("terlambat"),
                func.sum(case((Attendance.status == "Early leave", 1), else_=0)).label("early_leave"),
                func.sum(case((Attendance.status == "Lembur", 1), else_=0)).label("lembur"),
            )
            .filter(
                Attendance.emp_id == user.id,
                Attendance.isact == True,
                Attendance.date.between(start_date, end_date)
            )
            .group_by(Attendance.date)
            .order_by(Attendance.date.desc())
        ).fetchall()

        # Prepare header data
        header = HeaderAbsensi(
            total=sum(1 if row.total > 0 else 0 for row in grouped_data),
            hadir=sum(1 if row.hadir > 0 else 0 for row in grouped_data),
            absen=sum(1 if row.absen > 0 else 0 for row in grouped_data),
            sakit=sum(1 if row.sakit > 0 else 0 for row in grouped_data),
            cuti=sum(1 if row.cuti > 0 else 0 for row in grouped_data),
            izin=sum(1 if row.izin > 0 else 0 for row in grouped_data),
            terlambat=sum(1 if row.terlambat > 0 else 0 for row in grouped_data),
            early_leave=sum(1 if row.early_leave > 0 else 0 for row in grouped_data),
            lembur=sum(1 if row.lembur > 0 else 0 for row in grouped_data),
        )

        # Prepare history data
        history = []
        for att in data_att:
            if att.status in ("Absen", "Sakit", "Cuti", "Izin"):
                continue
            outlet = db.execute(
                select(ClientOutlet).filter(ClientOutlet.id == att.loc_id)
            ).scalar_one_or_none()

            # Calculate duration
            if att.clock_in and att.clock_out:
                # Combine clock_in and clock_out with a date to calculate the duration
                clock_in_datetime = datetime.combine(att.date, att.clock_in)
                clock_out_datetime = datetime.combine(att.date, att.clock_out)
                duration_seconds = (clock_out_datetime - clock_in_datetime).total_seconds()
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                duration = f"{hours} jam {minutes} menit"
            else:
                duration = None

            history.append(
                HistoryAbsensi_Menuabsensi(
                    id=att.id,
                    date=att.date.strftime("%d %B %Y") if att.clock_in else None,
                    clock_in=att.clock_in.strftime("%H:%M") if att.clock_in else None,
                    clock_out=att.clock_out.strftime("%H:%M") if att.clock_out else None,
                    outlet=DataOutlet(
                        id=outlet.id if outlet else None,
                        name=outlet.name if outlet else None,
                        address=outlet.address if outlet else None,
                        latitude=outlet.latitude if outlet else 0.0,
                        longitude=outlet.longitude if outlet else 0.0,
                    ),
                    duration=duration
                )
            )

        return DataMenuAbsensi(
            this_month=today.strftime("%B %Y"),
            header=header, 
            history=history
            ).dict()
    except Exception as e:
        print("Error get menu absensi: \n", e)
        raise ValueError("Failed get menu absensi")


# Haversine formula to calculate distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in kilometers
    dlat = radians(lat2 - float(lat1))
    dlon = radians(lon2 - float(lon1))
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c * 1000

async def get_menu_checkout(
    db: Session,
    user: User,
) -> DataMenuCheckout:
    try:
        # Data preparation
        today = datetime.now(timezone(TZ)).date()
        att_data = db.execute(
            select(Attendance)
            .filter(
                Attendance.isact == True,
                Attendance.emp_id == user.id,
                Attendance.date == today,
            )
            .order_by(Attendance.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if not att_data:
            raise ValueError("Attendance not found")

        # Get the outlet based on loc_id in Attendance
        outlet = db.execute(
            select(ClientOutlet).filter(ClientOutlet.id == att_data.loc_id)
        ).scalar_one_or_none()
        if not outlet:
            raise ValueError("Outlet not found")

        # Haversine formula to calculate distance
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Radius of Earth in kilometers
            dlat = radians(lat2 - float(lat1))
            dlon = radians(lon2 - float(lon1))
            a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        # Calculate distance between user and outlet in kilometers
        distance_m = haversine(att_data.latitude, att_data.longitude, outlet.latitude, outlet.longitude)

        return DataMenuCheckout(
            outlet=DataOutlet(
                id=outlet.id,
                name=outlet.name,
                address=outlet.address,
                latitude=outlet.latitude,
                longitude=outlet.longitude,
            ),
            user_latitude=att_data.latitude,
            user_longitude=att_data.longitude,
            distance=round(distance_m, 2),
            clock_in=att_data.clock_in.strftime("%H:%M"),
            clock_out=att_data.clock_out.strftime("%H:%M") if att_data.clock_out else None,
        ).dict()
    except Exception as e:
        print("Error get menu checkout: \n", e)
        raise ValueError("Failed get menu checkout")

async def get_list_leave(
    db: Session,
    user: User,
    src: Optional[str] = None,
) -> List[DataLeave]:
    try:
        # Query leave data for the user
        query_leaves = (
            select(LeaveTable).filter(
                LeaveTable.emp_id == user.id,
                LeaveTable.isact == True
            )
        )
        if src:
            query_leaves = query_leaves.filter(
                or_(
                LeaveTable.type == src, 
                LeaveTable.note.ilike(f"%{src}%")
                )
            )
        leaves = db.execute(
            query_leaves
        ).scalars().all()

        # Format the leave data
        result = []
        for leave in leaves:
            start_date = leave.start_date.strftime("%d %B")
            end_date = leave.end_date.strftime("%d %B %Y")
            total_days = (leave.end_date - leave.start_date).days + 1
            date_information = f"{start_date} - {end_date} ({total_days} days)"

            result.append(
                DataLeave(
                    id=leave.id,
                    type=leave.type,
                    status=Organization(
                        id=leave.status_leave.id if leave.status_leave else None,
                        name=leave.status_leave.name if leave.status_leave else None
                        ),
                    note=leave.note,
                    evidence=leave.evidence,
                    date_information=date_information,
                ).dict()
            )

        return result
    except Exception as e:
        print("Error get list leave: \n", e)
        raise ValueError("Failed get list leave")



async def check_nearest_outlet(
    data_latitude:float,
    data_longitude:float,
    db:Session,
    user:User
):
    try:
        # Get all outlet
        outlets = db.execute(
            select(ClientOutlet).filter(ClientOutlet.client_id==user.client_id)
        ).scalars().all()

        # Haversine formula to calculate distance
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Radius of Earth in kilometers
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            return R * c

        # Get nearest outlet
        nearest_outlet = None
        nearest_distance = float('inf')
        for outlet in outlets:
            distance = haversine(outlet.latitude, outlet.longitude, data_latitude, data_longitude)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_outlet = outlet

        return DataOutlet(
            id=nearest_outlet.id,
            name=nearest_outlet.name,
            address=nearest_outlet.address,
            latitude=nearest_outlet.latitude,
            longitude=nearest_outlet.longitude
        ).dict()
    except Exception as e:
        print("Error check nearest outlet: \n", e)
        raise ValueError("Failed check nearest outlet")

async def add_checkin(
    db:Session,
    data:CheckinRequest,
    user:User,
    status:str="Hadir"
):
    try:
        # Data Preparation
        data_outlet = db.execute(
            select(ClientOutlet).filter(ClientOutlet.id==data.outlet_id)
        ).scalar()
        if not data_outlet:
            raise ValueError("Outlet not found")
        # Calculate distance
        distance_m = haversine(data.latitude, data.longitude, data_outlet.latitude, data_outlet.longitude)

        today = datetime.now(timezone(TZ)).date()
        today_name = datetime.now(timezone(TZ)).strftime("%A")  # Get day name like "Monday", "Tuesday", etc.
        shift = db.execute(
            select(ShiftSchedule).filter(ShiftSchedule.emp_id==user.id, 
                                         ShiftSchedule.day==today_name,
                                         ShiftSchedule.isact==True
                                         ).limit(1)
        ).scalar_one_or_none()
        if not shift:
            raise ValueError("Shift not found")
        
        # Check if user already checkin and not yet checkout
        query_attendance = db.execute(
            select(Attendance).filter(
                Attendance.emp_id==user.id, 
                Attendance.isact==True,
                Attendance.date==today,
                Attendance.clock_out==None,
                )
        )
        if query_attendance.scalar_one_or_none():
            raise ValueError("Already checkin")

        # Status Logic
        status = await check_first_attendance(
                db=db,
                today=today,
                user=user,
                shift=shift,
                status=status,
            )

        # Insert data
        checkin = Attendance(
            emp_id=user.id,
            client_id=user.client_id,
            loc_id=data.outlet_id,
            clock_in=datetime.now(timezone(TZ)),
            status=status,
            date=today,
            longitude=data.longitude,
            latitude=data.latitude,
            isact=True,
            created_by=user.id,
            created_at=datetime.now(timezone(TZ)),
            distance=distance_m,
        )

        db.add(checkin)
        db.commit()
        return "OK"
    except ValueError as e:
        raise ValueError(e)
    except Exception as e:
        print("Error add checkin: \n", e)
        raise ValueError("Failed checkin")
    
async def check_first_attendance(
    db:Session,
    today:any,
    user:User,
    shift:any,
    status:str,
):
    try:
        query_count_attendance = db.execute(
            select(func.count(Attendance.id)).filter(
                Attendance.emp_id==user.id, 
                Attendance.isact==True,
                Attendance.date==today,
                )
        )
        query_attendance = query_count_attendance.scalar()
        if query_attendance == 0:
            checkin = datetime.now(timezone(TZ))
            if shift.time_start <= checkin.time():
                status = "Terlambat"
        return status
    except Exception as e:
        raise ValueError(e)

async def add_checkout(
    db:Session,
    data:CheckoutRequest,
    user:User,
    status:str="Hadir",
    background_tasks:any=None,
):
    try:
        # Data Preparation
        today = datetime.now(timezone(TZ)).date()
        today_name = datetime.now(timezone(TZ)).strftime("%A")  # Get day name like "Monday", "Tuesday", etc.
        shift = db.execute(
            select(ShiftSchedule).filter(ShiftSchedule.emp_id==user.id, 
                                         ShiftSchedule.day==today_name,
                                         ShiftSchedule.isact==True
                                         ).limit(1)
        ).scalar_one_or_none()
        if not shift:
            raise ValueError("Shift not found")
        query_attendance = db.execute(
            select(Attendance).filter(
                Attendance.emp_id==user.id, 
                Attendance.isact==True,
                Attendance.date==today,
                Attendance.clock_out==None,
                )
        )
        # Insert data
        checkout = query_attendance.scalar_one_or_none()
        if not checkout:
            raise ValueError("Attendance not found")
        # Status Logic
        checkout.clock_out = datetime.now(timezone(TZ))
        # Ensure checkout.clock_in has timezone if it doesn't
        if checkout.clock_in.tzinfo is None:
            checkout.clock_in = checkout.clock_in.replace(tzinfo=timezone(TZ))
            
        if checkout.status == "Terlambat":
            checkout.status = "Terlambat"
        elif shift.time_end >= checkout.clock_out.time():
            checkout.status = "Early leave"
        elif (checkout.clock_out - datetime.combine(today, shift.time_end).replace(tzinfo=timezone(TZ))).total_seconds() > 2 * 3600:
            checkout.status = "Lembur"
        else:
            checkout.status = status

        # Data Timesheet preparation
        if checkout.clock_in.tzinfo is None:
            checkout.clock_in = timezone(TZ).localize(checkout.clock_in)
        if checkout.clock_out.tzinfo is None:
            checkout.clock_out = timezone(TZ).localize(checkout.clock_out)

        # Calculate Duration
        if isinstance(checkout.clock_in, datetime) and isinstance(checkout.clock_out, datetime):
            time_diff = checkout.clock_out - checkout.clock_in
        else:
            clock_in_dt = checkout.clock_in if isinstance(checkout.clock_in, datetime) else datetime.combine(today, checkout.clock_in).replace(tzinfo=timezone(TZ))
            clock_out_dt = checkout.clock_out if isinstance(checkout.clock_out, datetime) else datetime.combine(today, checkout.clock_out).replace(tzinfo=timezone(TZ))
            time_diff = clock_out_dt - clock_in_dt
            
        # We need to extract hours, minutes, seconds from the timedelta to create a time object
        total_seconds = time_diff.total_seconds()
        
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Handle potential overflow for hours (MySQL TIME can store values up to 838:59:59)
        hours = min(hours, 838)

        time_duration = time(hour=hours, minute=minutes, second=seconds)
        
        # Properly handle the datetime conversion for TimeSheet
        if clock_in_dt.tzinfo is None:
            clock_in_dt = clock_in_dt.replace(tzinfo=timezone(TZ))
        if clock_out_dt.tzinfo is None:
            clock_out_dt = clock_out_dt.replace(tzinfo=timezone(TZ))

        # Create a dictionary of timesheet data
        timesheet_data = {
            "emp_id": user.id,
            "client_id": user.client_id,
            "clock_in": clock_in_dt,
            "clock_out": clock_out_dt,
            "total_hours": time_duration,
            "note": data.note,
            "created_by": user.id,
            "created_at": datetime.now(timezone(TZ)),
            "isact": True,
            "outlet_id": checkout.loc_id,
        }

        background_tasks.add_task(
            add_timesheet,
            timesheet_data
        )

        checkout.updated_by = user.id
        checkout.updated_at = datetime.now(timezone(TZ))
        db.add(checkout)
        db.commit()
        return "OK"
        
    except Exception as e:
        print("Error add checkout: \n", e)
        raise ValueError("Failed checkout")

async def add_timesheet(
    payload:Type[any]
):
    db = SessionLocal()  # Get connection from pool
    try:
        print("Starting TimeSheet addition")
        new_timesheet = TimeSheet(
            **payload
        )
        db.add(new_timesheet)
        db.commit()
        return True
    except Exception as e:
        db.rollback()  # Rollback any changes on error
        print(f"Error adding timesheet: {str(e)}")
        # Log the error but don't raise exception in background task
        return False
    finally:
        db.close()  # Always ensure connection is closed properly
    
async def add_izin(
    db: Session,
    data: LeaveRequest,
    user: User,
):
    try:
        # Data Preparation
        izin_query = db.execute(
            select(Izin).filter(Izin.id == data.leave_id)
        )
        izin = izin_query.scalar_one_or_none()
        if not izin:
            raise ValueError("Izin not found")

        # Validate date range
        start_date = datetime.strptime(data.start_date, "%d-%m-%Y").date()
        end_date = datetime.strptime(data.end_date, "%d-%m-%Y").date()
        if start_date > end_date:
            raise ValueError("Start date cannot be later than end date")

        # Create attendance record
        checkin = Attendance(
            emp_id=user.id,
            client_id=user.client_id,
            status=izin.name,
            isact=True,
            created_by=user.id,
            created_at=datetime.now(timezone(TZ)),
        )
        db.add(checkin)
        db.commit()
        db.refresh(checkin)

        # Create leave record
        leave = LeaveTable(
            atendance_id=checkin.id,
            emp_id=user.id,
            created_by=user.id,
            start_date=start_date,
            end_date=end_date,
            note=data.note,
            evidence=data.evidence,
            type=izin.name,
            status=1,
        )
        db.add(leave)
        db.commit()

        return {"message": "Leave request added successfully", "leave_id": leave.id}

    except Exception as e:
        if 'checkin' in locals() and checkin.id:
            checkin.isact = False
            db.add(checkin)
            db.commit()
        # Log the error
        print("Error add izin: \n", e)  # Replace with proper logging in production
        raise ValueError("Failed izin")


