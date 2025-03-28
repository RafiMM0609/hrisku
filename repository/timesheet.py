from typing import Optional, List, Type
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
from models.TimeSheet import TimeSheet
from models.Izin import Izin
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
    HistoryAbsensi,
    HeaderAbsensi,
    CheckAttendance,
    DataMenuTimeSheet,
    DataHeaderTimeSheet,
    ListTimesheet,
    CoCiTimesheet,
    HistoryAbsensi,
    DetailTimesheet,
)

async def get_detail_timesheet(
    db:Session,
    user:User,
    id_timesheet:int,
)->DetailTimesheet:
    try:
        query_timesheet = (
            select(TimeSheet)
            .filter(TimeSheet.id==id_timesheet)
            .filter(TimeSheet.isact==True)
            .limit(1)
        )
        data_timesheet = db.execute(query_timesheet).scalar_one_or_none()
        if not data_timesheet:
            return DetailTimesheet()
        start_time = data_timesheet.clock_in.time()
        end_time = data_timesheet.clock_out.time()
        # History data preparation
        today = data_timesheet.clock_in.date()
        day_start = datetime.combine(today, time.min)
        day_end = datetime.combine(today, time.max)
        
        # Query attendance data with datetime filter
        query_data_att = (
            select(TimeSheet).filter(
            TimeSheet.emp_id == user.id,
            TimeSheet.isact == True,
            TimeSheet.clock_in >= day_start,
            TimeSheet.clock_in <= day_end
            )
            .join(ClientOutlet, TimeSheet.outlet_id == ClientOutlet.id, isouter=True)
        )
        query_data_att = query_data_att.order_by(TimeSheet.clock_in.desc())

        data_att = db.execute(
            query_data_att
            .limit(100)
        ).scalars().all()
        history = []
        for item in data_att:
            history.append(
                HistoryAbsensi(
                    clock_in=item.clock_in.strftime("%H:%M") if item.clock_in else None,
                    clock_out=item.clock_out.strftime("%H:%M") if item.clock_out else None,
                    date=item.clock_in.strftime("%d %B %Y") if item.clock_in else None,
                    duration=item.total_hours.strftime("%H:%M"),
                    outlet=DataOutlet(
                        id=item.outlets.id if item.outlets else None,
                        name=item.outlets.name if item.outlets else None,
                        address=item.outlets.address if item.outlets else None,
                        latitude=item.outlets.latitude if item.outlets else 0.0,
                        longitude=item.outlets.longitude if item.outlets else 0.0,
                    )
                )
            )

        return DetailTimesheet(
            work_type="Shift",
            work_day=today.strftime("%A"),
            work_hours=f"{start_time}-{end_time}",
            work_model="WFO",
            history=history
        ).dict()
    except Exception as e:
        print("Error get detail timesheet: \n", e)
        raise ValueError("Failed get detail timesheet")

async def get_data_menu_timesheet(
    db:Session,
    user:User,
    bulan:Optional[str]=None,
)->DataMenuTimeSheet:
    try:
        # Get current date in the application timezone
        if bulan:
            today = datetime.strptime(bulan, "%Y-%m-%d").date()
        else:
            today = datetime.now(timezone(TZ)).date()
        today_day_name = today.strftime("%A")  # Get day name (Monday, Tuesday, etc.)
        
        # Get the first and last day of current month
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) if first_day_of_month.month < 12 
                    else first_day_of_month.replace(year=first_day_of_month.year + 1, month=1, day=1)) - timedelta(days=1)
        
        # Get user's shift schedule for today specifically
        user_shift = db.execute(
            select(ShiftSchedule)
            .filter(
                ShiftSchedule.emp_id == user.id,
                ShiftSchedule.isact == True,
                ShiftSchedule.day == today_day_name  # Filter by day of week
            )
        ).scalar_one_or_none()
        
        # Get dates from Attendance table for the current month
        attendance_dates = db.execute(
            select(func.date(Attendance.date).label("date"))
            .filter(
                Attendance.emp_id == user.id,
                Attendance.isact == True,
                Attendance.date.between(first_day_of_month, last_day_of_month)
            )
            .group_by(func.date(Attendance.date))
            .order_by(func.date(Attendance.date).asc())
        ).scalars().all()
        
        # Format the dates to match the required format
        calendar_dates = [date.strftime("%Y-%m-%d") for date in attendance_dates] if attendance_dates else []
        
        # Prepare header data with shift information
        header = DataHeaderTimeSheet(
            start_shift=user_shift.time_start.strftime("%H:%M") if user_shift and user_shift.time_start else None,
            end_shift=user_shift.time_end.strftime("%H:%M") if user_shift and user_shift.time_end else None,
            total_jam=None  # Will calculate if we have clock-in and clock-out
        )
        
        # Calculate total_jam from shift if available
        if user_shift and user_shift.time_start and user_shift.time_end:
            # Convert time objects to datetime for calculation
            start_dt = datetime.combine(datetime.today(), user_shift.time_start)
            end_dt = datetime.combine(datetime.today(), user_shift.time_end)
            
            # Handle overnight shifts (when end time is earlier than start time)
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
                
            # Calculate hours difference
            shift_duration_seconds = (end_dt - start_dt).total_seconds()
            header.total_jam = round(shift_duration_seconds / 3600, 1)  # Convert to hours with 1 decimal
        
        # Get all timesheet records for this month (limited to 100)
        # Create datetime objects for first and last day of month (with time)
        first_day_datetime = datetime.combine(first_day_of_month, time.min)
        last_day_datetime = datetime.combine(last_day_of_month, time.max)
        
        # Convert to timezone aware if needed
        if TZ:
            first_day_datetime = timezone(TZ).localize(first_day_datetime)
            last_day_datetime = timezone(TZ).localize(last_day_datetime)
        
        # Query timesheets with proper datetime filtering
        month_timesheets = db.execute(
            select(TimeSheet)
            .filter(
                TimeSheet.emp_id == user.id,
                TimeSheet.isact == True,
                TimeSheet.clock_in >= first_day_datetime,
                TimeSheet.clock_in <= last_day_datetime
            )
            .order_by(TimeSheet.clock_in.desc())
            .limit(100)  # Limit to 100 records
        ).scalars().all()
        
        # Prepare activity list with timesheet information
        activities = []
        
        # Process all timesheet entries for the month (up to 100 records)
        for ts in month_timesheets:
            ts_date = ts.clock_in.date()
            
            # Get outlet information
            outlet = db.execute(
                select(ClientOutlet).filter(ClientOutlet.id == ts.outlet_id)
            ).scalar_one_or_none()
            
            # Calculate total hours if both clock-in and clock-out exist
            total_hours = None
            if ts.clock_in and ts.clock_out:
                duration_seconds = (ts.clock_out - ts.clock_in).total_seconds()
                total_hours = int(duration_seconds // 3600)  # Convert to hours
                
                # Update header with today's total hours
                if ts_date == today:
                    header.total_jam = total_hours
            
            # Create activity object
            activities.append(
                ListTimesheet(
                    date=ts_date.strftime("%d %B %Y"),
                    coci=CoCiTimesheet(
                        id=ts.id,
                        start_shift=ts.clock_in.strftime("%H:%M") if ts.clock_in else None,
                        end_shift=ts.clock_out.strftime("%H:%M") if ts.clock_out else None,
                        note=ts.note,
                        outlet=DataOutlet(
                            id=outlet.id if outlet else None,
                            name=outlet.name if outlet else None,
                            address=outlet.address if outlet else None,
                            latitude=outlet.latitude if outlet else 0.0,
                            longitude=outlet.longitude if outlet else 0.0,
                        )
                    ),
                    total_jam=total_hours
                )
            )
        
        # Return the complete DataMenuTimeSheet object with list of activities (limited to 100)
        return DataMenuTimeSheet(
            header=header,
            calender=calendar_dates,
            activity=activities
        ).dict()
    except Exception as e:
        print("Error get data menu timesheet: \n", e)
        raise ValueError("Failed get data menu timesheet")

async def get_status_attendance(
  db: Session,
  user: User,      
)->CheckAttendance:
    try:
        today = datetime.now(timezone(TZ)).date()
        data_attendance = db.execute(
            select(Attendance).filter(
                Attendance.emp_id == user.id,
                Attendance.isact == True,
                Attendance.date == today,
                Attendance.clock_out == None,
            )
        ).scalar_one_or_none()
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
        raise ValueError("Failed get status attendance")

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
        
        # Default date range - current month
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) if first_day_of_month.month < 12 
                    else first_day_of_month.replace(year=first_day_of_month.year + 1, month=1, day=1)) - timedelta(days=1)
        
        # Override with parameters if provided
        start_date = datetime.strptime(start, "%d-%m-%Y").date() if start else first_day_of_month
        end_date = datetime.strptime(end, "%d-%m-%Y").date() if end else last_day_of_month
        
        # Query attendance data with date filter
        query_data_att = (
            select(Attendance).filter(
            Attendance.emp_id == user.id,
            Attendance.isact == True,
            Attendance.date.between(start_date, end_date)
            )
            .join(ClientOutlet, Attendance.loc_id == ClientOutlet.id, isouter=True)
        )
        if src:
            query_data_att = query_data_att.filter(
                or_(
                    ClientOutlet.name.ilike(f"%{src}%")
                )
            )
        if order == "asc":
            query_data_att = query_data_att.order_by(Attendance.date.asc())
        elif order == "desc":
            query_data_att = query_data_att.order_by(Attendance.date.desc())

        data_att = db.execute(
            query_data_att
            .limit(100)
        ).scalars().all()
        
        if not data_att:
            return DataMenuAbsensi(
            this_month=today.strftime("%B %Y"),
            header=HeaderAbsensi(), 
            history=[]
            ).dict()
        
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
                HistoryAbsensi(
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