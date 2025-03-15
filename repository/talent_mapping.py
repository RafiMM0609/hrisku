from typing import Optional, List
import secrets
from math import ceil
from sqlalchemy import select, func
from sqlalchemy.orm import Session, aliased
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local
from models.User import User
from models.Role import Role
from models.Client import Client
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.talent_mapping import (
    ListAllUser,
    RegisTalentRequest,
)
import os
import asyncio

async def add_user_validator(db: Session, payload: RegisTalentRequest):
    try:
        errors = None
        queries = []

        if payload.phone:
            queries.append(select(User.id).filter(User.phone == payload.phone).exists())

        if payload.email:
            queries.append(select(User.id).filter(User.email == payload.email).exists())

        if queries:
            result = db.execute(select(*queries)).fetchall()

            if payload.role_id and result[0][0]:  # Cek role_id
                errors = "Phone number already used"

            if payload.email and result[0][1]:  # Cek email
                errors = "Email already exists"
        if errors:
            return {"success": False, "errors": errors}
        return {"success": True}

    except Exception as e:
        print(f"Validation error: {e}")

async def regist_talent(
    db: Session,
    user:User,
    payload: RegisTalentRequest,
    role_id: int = 1,
):
    try:
        role = db.execute(
            select(Role)
            .filter(Role.id==role_id)).scalar()
        new_user = User(
            photo=payload.photo,
            name=payload.name,
            birth_date=payload.dob,
            nik=payload.nik,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            client_id=payload.client_id
        )
        new_user.roles.append(role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        print("Error regis talent : \n", e)
        raise ValueError("Failed regis talent")

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
            "dob": d.birth_date,
            "nik": d.nik,
            "email": d.email,
            "phone": d.phone,
            "address": d.address,
        })
    return ls_data