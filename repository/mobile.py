from typing import Optional
from math import ceil
import secrets
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session, aliased
from models.User import User
from models.Role import Role
from models.Attendance import Attendance
from models.ShiftSchedule import ShiftSchedule
from models.LeaveTable import LeaveTable
from models.Outlet import Outlet
from models.Client import Client
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.mobile import (
    CheckinRequest,
    CheckoutRequest,
    LeaveRequest
)
import os
import asyncio

async def add_chekin(
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
        # Insert data
        checkin = Attendance(
            emp_id=user.id,
            client_id=user.client_id,
            loc_id=data.outlet_id,
            clock_in=datetime.now(timezone(TZ)),
            status=status,
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
            select(Attendance).filter(Attendance.id==data.attendance_id, Attendance.isact==True)
        )
        # Insert data
        checkout = query_attendance.scalar_one_or_none()
        if not checkout:
            raise ValueError("Attendance not found")
        checkout.clock_out = datetime.now(timezone(TZ))
        # checkout.status = status if shift.time_end >= checkout.clock_out.time() else "Terlambat"
        checkout.status = status if shift.time_end <= checkout.clock_out.time() else "Lembur"
        checkout.updated_by = user.id
        checkout.updated_at = datetime.now(timezone(TZ))
        db.add(checkout)
        db.commit()
        return "OK"
        
    except Exception as e:
        print("Error add checkout: \n", e)
        raise ValueError("Failed checkout")
    
async def add_izin(
    db:Session,
    data:LeaveRequest,
    user:User,
    type:str="Izin",
):
    try:
        checkin = Attendance(
            emp_id=user.id,
            client_id=user.client_id,
            status=type,
            isact=True,
            created_by=user.id,
            created_at=datetime.now(timezone(TZ)),
        )
        db.add(checkin)

        leave = LeaveTable(
            start_date=data.start_date,
            end_date=data.end_date,
            note=data.note,
            evidence=data.evidence,
            type=type,
        )
        db.add(leave)
        db.commit()
    except Exception as e:
        print("Error add izin: \n", e)
        raise ValueError("Failed izin")
    

    