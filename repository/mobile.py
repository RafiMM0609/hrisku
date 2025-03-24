from typing import Optional, List
from math import ceil, radians, sin, cos, sqrt, atan2  # Add these imports for Haversine formula
import secrets
from sqlalchemy import select, func, distinct, or_, and_  # Added and_ import
from sqlalchemy.orm import Session, aliased
from models.User import User
from models.Role import Role
from models.Attendance import Attendance
from models.ShiftSchedule import ShiftSchedule
from models.LeaveTable import LeaveTable
from models.ClientOutlet import ClientOutlet
from models.Izin import Izin
from datetime import datetime, timedelta
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

)

async def get_menu_absensi(
    db: Session,
    user: User,
    src: Optional[str] = None,
) -> DataMenuAbsensi:
    try:
        # Data preparation
        # query_data_att = (
        #     select(Attendance).filter(
        #         Attendance.emp_id == user.id,
        #         Attendance.isact == True
        #     ).limit(100)
        # )
        data_att = db.execute(
            select(Attendance).filter(
                Attendance.emp_id == user.id,
                Attendance.isact == True
            ).limit(100)
        ).scalars().all()
        if not data_att:
            return []
        
        # Prepare header data
        today = datetime.now(timezone(TZ)).date()
        header = HeaderAbsensi(
            total=len(data_att),
            hadir=sum(1 for att in data_att if att.status == "Hadir"),
            absen=sum(1 for att in data_att if att.status == "Absen"),
            sakit=sum(1 for att in data_att if att.status == "Sakit"),
            cuti=sum(1 for att in data_att if att.status == "Cuti"),
            izin=sum(1 for att in data_att if att.status == "Izin"),
            terlambat=sum(1 for att in data_att if att.status == "Terlambat"),
            early_leave=sum(1 for att in data_att if att.status == "Early leave"),
            lembur=sum(1 for att in data_att if att.status == "Lembur"),
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
        distance = haversine(att_data.latitude, att_data.longitude, outlet.latitude, outlet.longitude)
        # In centimeters
        distance_cm = distance * 100000

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
            distance=round(distance_cm, 2),
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
        # Check if user already checkin
        query_attendance = db.execute(
            select(Attendance).filter(
                Attendance.emp_id==user.id, 
                Attendance.isact==True,
                Attendance.date==today,
                )
        )
        if query_attendance.scalar_one_or_none():
            raise ValueError("Already checkin")

        # Status Logic
        checkin = datetime.now(timezone(TZ))
        if shift.time_start <= checkin.time():
            status = "Terlambat"

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
        )

        db.add(checkin)
        db.commit()
        return "OK"
        
    except Exception as e:
        print("Error add checkin: \n", e)
        raise ValueError("Failed checkin")

async def add_checkout(
    db:Session,
    data:CheckoutRequest,
    user:User,
    status:str="Hadir"
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
                Attendance.date==today
                )
        )
        # Insert data
        checkout = query_attendance.scalar_one_or_none()
        if not checkout:
            raise ValueError("Attendance not found")
        # Status Logic
        checkout.clock_out = datetime.now(timezone(TZ))
        if checkout.status == "Terlambat":
            checkout.status = "Terlambat"
        elif shift.time_end >= checkout.clock_out.time():
            checkout.status = "Early leave"
        elif (checkout.clock_out - datetime.combine(today, shift.time_end)).total_seconds() > 2 * 3600:
            checkout.status = "Lembur"
        else:
            checkout.status = status

        checkout.updated_by = user.id
        checkout.updated_at = datetime.now(timezone(TZ))
        db.add(checkout)
        db.commit()
        return "OK"
        
    except Exception as e:
        print("Error add checkout: \n", e)
        raise ValueError("Failed checkout")
    
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


