from typing import Optional, List
import secrets
from math import ceil
from sqlalchemy import select, func
from sqlalchemy.orm import Session, aliased
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local, generate_link_download
from models.User import User
from models.Role import Role
from models.Client import Client
from models.ClientOutlet import ClientOutlet
from models.ShiftSchedule import ShiftSchedule
from models.UserRole import UserRole
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.talent_monitor import (
    ListAllUser,
    TalentInformation,
    Organization,
    TalentMapping,
    DataWorkingArrangement,
    DataOutlet
)
import os
import asyncio

async def data_talent_mapping(
    db: Session,
    talent_id: str,
) -> TalentMapping:
    """
    Get talent mapping data by talent_id including client and outlet information
    """
    try:
        # Get user with client and outlet relationship
        query = select(
            User, 
            Client, 
            Client.name.label("client_name"),
            ClientOutlet,
            ClientOutlet.name.label("outlet_name")
        ).join(
            Client, User.client_id == Client.id
        ).join(
            ClientOutlet, User.outlet_id == ClientOutlet.id
        ).filter(
            User.id_user == talent_id,
            User.isact == True
        ).limit(1)
        
        result = db.execute(query).first()
        
        if not result:
            raise ValueError("Talent not found or has no mapping information")
        
        user, client, client_name, outlet, outlet_name = result
        
        # Get shift information
        shift_query = select(ShiftSchedule).filter(
            ShiftSchedule.emp_id == user.id,
            ShiftSchedule.isact == True
        )
        shifts = db.execute(shift_query).scalars().all()
        
        # Format shift data
        shift_data = []
        for shift in shifts:
            shift_data.append({
                "shift_id": shift.id_shift,
                "day": shift.day,
                "start_time": shift.time_start.strftime("%H:%M") if shift.time_start else "08:00",
                "end_time": shift.time_end.strftime("%H:%M") if shift.time_end else "15:00"
            })
        
        # Create output
        return TalentMapping(
            talent_id=user.id_user,
            name=user.name,
            dob=user.birth_date.strftime("%d-%m-%Y") if user.birth_date else "22-12-31",
            nik=user.nik if user.nik else "",
            email=user.email,
            phone=user.phone,
            address=user.address,
            client=Organization(id=client.id, name=client_name),
            outlet=Organization(id=outlet.id, name=outlet_name),
            workdays=shifts[0].workdays if shifts and shifts[0].workdays else 0,
            shift=shift_data
        )
        
    except Exception as e:
        print(f"Error getting talent mapping: {e}")
        raise ValueError(f"Failed to get talent mapping data: {str(e)}")

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
        photo=generate_link_download(d.photo) if d.photo else ""
    )

async def list_talent(
    db: Session,
    page: int,
    page_size: int,
    src: Optional[str] = None
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
            )
            .filter(User.isact == True))

        # Query count untuk paginasi
        query_count = (select(func.count(User.id))
                       .filter(User.isact == True))

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
        })
    return ls_data