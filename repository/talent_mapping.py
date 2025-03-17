from typing import Optional, List
import secrets
from math import ceil
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session, aliased
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local
from models.User import User
from models.Role import Role
from models.ShiftSchedule import ShiftSchedule
from models.Client import Client
from models.ClientOutlet import ClientOutlet
from models import SessionLocal
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.talent_mapping import (
    ListAllUser,
    RegisTalentRequest,
    EditTalentRequest,
)
import os
import asyncio

async def add_user_validator(db: Session, payload: RegisTalentRequest):
    try:
        errors = None
        queries = []

        if payload.outlet_id and payload.client_id:
            queries.append(select(ClientOutlet.id).filter(ClientOutlet.id == payload.outlet_id, ClientOutlet.client_id==payload.client_id ,ClientOutlet.isact==True).exists())

        if payload.email:
            queries.append(select(User.id).filter(User.email == payload.email, User.isact==True).exists())

        if payload.client_id:
            queries.append(select(Client.id).filter(Client.id == payload.client_id, Client.isact==True).exists())


        if queries:
            result = db.execute(select(*queries)).fetchall()

            if payload.client_id and payload.outlet_id and not result[0][0]:  # Cek outlet
                errors = "Outlet not valid"

            if payload.email and result[0][1]:  # Cek email
                errors = "Email already exists"

            if payload.client_id and not result[0][2]:  # Cek client
                errors = "Client not found"

        if errors:
            return {"success": False, "errors": errors}
        return {"success": True}

    except Exception as e:
        print(f"Validation error: {e}")

async def add_talent(
    db: Session,
    user:User,
    background_tasks:any,
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
            birth_date=datetime.strptime(payload.dob, "%d-%m-%Y").date(),
            nik=payload.nik,
            outlet_id=payload.outlet_id,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            client_id=payload.client_id
        )
        new_user.roles.append(role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.execute(
        update(User).where(User.id == new_user.id).values(id_user=await create_custom_id(new_user.id_seq))
        )
        db.commit()
        if isinstance(payload.shift, (list, tuple)):
            # await mapping_schedule(
            #     db, 
            #     new_user.client_id,
            #     new_user.id, 
            #     payload.shift, 
            #     payload.workdays
            # )
            background_tasks.add_task(
                add_mapping_schedule,
                new_user.client_id,
                new_user.id, 
                payload.shift, 
                payload.workdays
            )
    except Exception as e:
        print("Error regis talent : \n", e)
        raise ValueError("Failed regis talent")

async def add_mapping_schedule(client_id, emp_id, shift, workdays):
    db = SessionLocal()  # Ambil koneksi dari pool
    try:
        for item in shift:
            new_shift= ShiftSchedule(
                emp_id=emp_id,
                client_id=client_id,
                workdays=workdays,
                time_start=datetime.strptime(item.start_time, "%H:%M").time(),
                time_end=datetime.strptime(item.end_time, "%H:%M").time(),
                day=item.day,
                created_at=datetime.now(tz=timezone(TZ)),
            )
            db.add(new_shift)
            db.commit()
            db.refresh(new_shift)
            db.execute(
            update(ShiftSchedule).where(
                ShiftSchedule.id == new_shift.id)
                .values(id_shift=await create_custom_id(new_shift.id))
            )
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in background add mapping task: {e}")
    finally:
        db.close()  # Jangan lupa close agar tidak bocor


async def mapping_schedule(db, client_id, emp_id, data, workdays):
    try:
        ls_shift = []
        for item in data:
            new_shift= ShiftSchedule(
                emp_id=emp_id,
                client_id=client_id,
                workdays=workdays,
                time_start=datetime.strptime(item.start_time, "%H:%M").time(),
                time_end=datetime.strptime(item.end_time, "%H:%M").time(),
                day=item.day,
                created_at=datetime.now(tz=timezone(TZ)),
            )
            ls_shift.append(new_shift)
        db.bulk_save_objects(ls_shift)
        db.commit()
    except Exception as e:
        db.rollback()
        print("Error mapping: \n", e)
        
async def create_custom_id(
        id: int, 
        prefix:Optional[str]="T"
) -> str:
    num_digits = len(str(id))
    formatted_id = f"{id:0{num_digits+1}d}"  
    return prefix + formatted_id

async def edit_user_validator(db: Session, payload: EditTalentRequest, id_user:str):
    try:
        errors = None
        queries = []

        if payload.outlet_id and payload.client_id:
            queries.append(select(ClientOutlet.id).filter(ClientOutlet.id == payload.outlet_id, ClientOutlet.client_id==payload.client_id ,ClientOutlet.isact==True).exists())

        if payload.email:
            queries.append(select(User.id).filter(User.email == payload.email, User.id_user!=id_user, User.isact==True).exists())

        if payload.client_id:
            queries.append(select(Client.id).filter(Client.id == payload.client_id, Client.isact==True).exists())


        if queries:
            result = db.execute(select(*queries)).fetchall()

            if payload.client_id and payload.outlet_id and not result[0][0]:  # Cek outlet
                errors = "Outlet not valid"

            if payload.email and result[0][1]:  # Cek email
                errors = "Email already exists"

            if payload.client_id and not result[0][2]:  # Cek client
                errors = "Client not found"

        if errors:
            return {"success": False, "errors": errors}
        return {"success": True}

    except Exception as e:
        print(f"Validation error: {e}")

async def edit_talent(
    db: Session,
    id_user: str,
    user:User,
    payload: RegisTalentRequest,
    role_id: int = 1,
):
    try:
        user_exist=db.execute(
            select(User)
            .filter(User.id_user==id_user)
            .limit(1)
        ).scalar()
        user_exist.photo=payload.photo
        user_exist.name=payload.name
        user_exist.birth_date=datetime.strptime(payload.dob, "%d-%m-%Y").date()
        user_exist.nik=payload.nik
        user_exist.outlet_id=payload.outlet_id
        user_exist.email=payload.email
        user_exist.phone=payload.phone
        user_exist.address=payload.address
        user_exist.client_id=payload.client_id
        user_exist.updated_by=user.id
        db.add(user_exist)
        db.commit()
        db.refresh(user_exist)
        db.commit()
        if isinstance(payload.shift, (list, tuple)):
            db.execute(
                update(ShiftSchedule)
                .where(ShiftSchedule.emp_id==user_exist.id)
                .values(isact=False)
            )
            db.commit()
            await mapping_schedule(
                db, 
                user_exist.client_id,
                user_exist.id, 
                payload.shift, 
                payload.workdays
            )
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
            "dob": d.birth_date.strftime("%d-%m-%Y") if d.birth_date else None,
            "nik": d.nik,
            "email": d.email,
            "phone": d.phone,
            "address": d.address,
        })
    return ls_data

async def detail_talent_mapping(
    db: Session,
    id_user: str,
):
    try:
        query = select(User).filter(User.id_user == id_user).limit(1)
        data = db.execute(query).scalar_one_or_none()
        
        if not data:
            raise ValueError("User not found")
    
        return await formating_detail(data)
    
    except Exception as e:
        print("Error detail mapping: \n", e)
        raise ValueError("Failed to get data")

async def formating_detail(data: User):
    return {
        "talent_id": data.id_user,
        "name": data.name,
        "dob": data.birth_date.strftime("%d-%m-%Y") if data.birth_date else None,
        "nik": data.nik,
        "email": data.email,
        "phone": data.phone,
        "address": data.address,
        "client": {
            "id": data.client_user.id if data.client_user else None,
            "name": data.client_user.name if data.client_user else None,
        },
        "outlet": {
            "id": data.user_outlet.id if data.user_outlet else None,
            "name": data.user_outlet.name if data.user_outlet else None,
        },
        "workdays": data.user_shift[0].workdays if data.user_shift else None,
        "shift": [
            {
                "shift_id": x.id_shift,
                "day": x.day,
                "start_time": x.time_start.strftime("%H:%M"),
                "end_time": x.time_end.strftime("%H:%M")
            } for x in (data.user_shift or []) if x.isact
        ]
    }
