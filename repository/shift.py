from typing import Optional
from math import ceil, radians, sin, cos, sqrt, atan2  # Add these imports for Haversine formula
import secrets
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session, aliased
from models.User import User
from models.ShiftSchedule import ShiftSchedule
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.shift import (
    DataShift
)

async def get_today_shift(
    db:Session,
    user:User,
):
    try:
        today = datetime.now(timezone(TZ)).date()
        today_name = datetime.now(timezone(TZ)).strftime("%A")  # Get day name like "Monday", "Tuesday", etc.
        shift = db.execute(
            select(ShiftSchedule).filter(ShiftSchedule.emp_id==user.id, 
                                         ShiftSchedule.day==today_name,
                                         ShiftSchedule.isact==True
                                         ).limit(1)
        ).scalar_one_or_none()
        if not shift:
            return None
        return DataShift(
            id=shift.id,
            day=shift.day,
            start=shift.time_start.strftime("%H:%M"),
            end=shift.time_end.strftime("%H:%M")
        ).dict()
    except Exception as e:
        print("Error get_today_shift", e)
        raise ValueError("Error get_today_shift")


