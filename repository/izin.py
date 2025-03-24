from typing import Optional
from math import ceil, radians, sin, cos, sqrt, atan2  # Add these imports for Haversine formula
import secrets
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session, aliased
from models.User import User
from models.Izin import Izin
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.izin import (
    DataIzin
)

async def get_izin_option(
    db:Session,
    user:User,
    src: Optional[str] = None
):
    try:
        query = select(Izin).limit(50)
        if src:
            query = query.filter(Izin.name.ilike(f"%{src}%"))
        izin = db.execute(query).scalars().all()
        return [DataIzin(
            id=i.id,
            name=i.name
        ).dict() for i in izin]
    except Exception as e:
        print("Error get_izin_option", e)
        raise ValueError("Error get_izin_option")


