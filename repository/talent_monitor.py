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
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.talent_mapping import (
    ListAllUser
)
import os
import asyncio

async def data_talent_information(
    db:Session,
    talent_id:str,
):
    try:
        query = select(User).filter(User.id_user == talent_id).limit(1)
        data = db.execute(query).scalar_one_or_none()
        
        if not data:
            raise ValueError("User not found")
    
        return await formating_talent_information(data)
    except Exception as e:
        print("Error data talent info: \n",e)
        raise ValueError("Failed get data detail informatoin")

async def formating_talent_information(d:User):
    return {
        "name": d.name,
        "role":{
            "id": d.roles[0].id if d.roles[0] else None,
            "name": d.roles[0].name if d.roles[0] else None
        },
        "talent_id": d.id_user,
        "dob": d.birth_date.strftime("%d-%m-%Y") if d.birth_date else None,
        "phone": d.phone,
        "address": d.address,
        "nik": d.nik,
        "email": d.email,
        "photo": generate_link_download(d.photo)
    }

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