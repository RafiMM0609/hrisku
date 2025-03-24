from typing import Optional
from math import ceil, radians, sin, cos, sqrt, atan2  # Add these imports for Haversine formula
import secrets
from sqlalchemy import select, func, distinct
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
)
import os
import asyncio

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
            dlon = radians(lat2 - lon1)
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
            checkout.status = "Early eave"
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


