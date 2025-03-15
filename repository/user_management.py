from typing import Optional
import secrets
from math import ceil
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session, aliased
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local
from models.User import User
from models.Role import Role
from models.UserRole import UserRole
from models.Client import Client
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.user_management import (
    AddUserRequest,
    EditUserRequest
)
import os
import asyncio


async def detail_user(
    db:Session,
    id_user:str,
):
    try:
        query = (
            select(
                User.id_user,
                User.name,
                User.email,
                User.phone,
                User.address,
                User.id,
            ).filter(User.id_user == id_user)
        )
        user = db.execute(query).first() 
        id_role = db.execute(
            select(UserRole.c.role_id).filter(UserRole.c.emp_id==user[5])
        ).first()
        role = db.execute(
            select(Role.id, Role.name).filter(Role.id==id_role[0])
        ).first()
        return await formated_detail(user, role)
    except Exception as e:
        print("Error get detail user : \n", e)
        raise ValueError("Failed get detail user")
    
async def formated_detail(user, role):
    obj = {
        "id_user" : user[0],
        "name":user[1],
        "email":user[2],
        "phone":user[3],
        "role":{
            "id":role[0],
            "name":role[1]
        },
        "address":user[4],
    }
    return obj

async def list_role(
    db:Session
):
    try:
        data = db.execute(
            select(
                Role.id, Role.name, Role)
        ).scalars().all()
    except Exception as e:
        raise ValueError(e)
    
async def add_user(
    db: Session,
    payload: AddUserRequest,
    user: User
):
    try:
        role = db.execute(
            select(Role).filter(Role.id == payload.role_id)
        ).scalar_one()
        if not role:
            raise ValueError("Role not found")
        password = secrets.token_urlsafe(16)
        # hashed_password = generate_hash_password(password)
        new_user = User(
            email=payload.email,
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
            first_login=password,
            created_by=user.id,
            photo=payload.photo,
        )
        new_user.roles.append(role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        new_user.id_user = await create_custom_id(new_user.id_seq)
        db.merge(new_user)  # Gunakan merge daripada add untuk menghindari error
        db.commit()
        return new_user
    except Exception as e:
        db.rollback()
        db.execute(
            (
                update(User)
                .where(User.id == new_user.id)
                .values(isact=False)
            )
        )
        db.commit()
        print("Error add user : \n", e)
        raise ValueError("Failed add user")
async def create_custom_id(
        id: int, 
        prefix:Optional[str]="U"
) -> str:
    num_digits = len(str(id))
    formatted_id = f"{id:0{num_digits+1}d}"  
    return prefix + formatted_id

    
async def add_user_validator(db: Session, payload: AddUserRequest):
    try:
        errors = None
        queries = []

        if payload.role_id:
            queries.append(select(Role.id).filter(Role.id == payload.role_id).exists())

        if payload.email:
            queries.append(select(User.id).filter(User.email == payload.email).exists())

        if queries:
            result = db.execute(select(*queries)).fetchall()

            if payload.role_id and not result[0][0]:  # Cek role_id
                errors = "Role not found"

            if payload.email and result[0][1]:  # Cek email
                errors = "Email already exists"
        if errors:
            return {"success": False, "errors": errors}
        return {"success": True}

    except Exception as e:
        print(f"Validation error: {e}")
async def edit_user_validator(
        db: Session, 
        payload: EditUserRequest,
        id:str
):
    try:
        errors = None
        queries = []

        if payload.role_id:
            queries.append(select(Role.id).filter(Role.id == payload.role_id).exists())

        if payload.email:
            queries.append(select(User).filter(User.id != id)
                .filter(User.email == payload.email).exists())

        if queries:
            result = db.execute(select(*queries)).fetchall()

            if payload.role_id and not result[0][0]:  # Cek role_id
                errors = "Role not found"

            if payload.email and result[-1][0]:  # Cek email
                errors = "Email already exists"
        if errors:
            return {"success": False, "errors": errors}
        return {"success": True}

    except Exception as e:
        print(f"Validation error: {e}")
async def edit_user(
    db: Session,
    payload: EditUserRequest,
    id: str,
    user: User
):
    try:
        user_exist = db.execute(
            select(User).filter(User.id_user == id)
        ).scalar_one()
        if not user_exist:
            raise ValueError("User not found")
        if payload.role_id:
            role = db.execute(
                select(Role).filter(Role.id == payload.role_id)
            ).scalar_one()
            if not role:
                raise ValueError("Role not found")
            user_exist.roles.clear()
            user_exist.roles.append(role)
        user_exist.name = payload.name
        user_exist.email = payload.email
        user_exist.phone = payload.phone
        user_exist.address = payload.address
        user_exist.phone = payload.phone
        user_exist.updated_by = user.id
        db.add(user_exist)
        db.commit()
        db.refresh(user_exist)
        return user_exist
    except Exception as e:
        print("Error edit user \n", e)
        raise ValueError("Failed edit user")
async def delete_user(
    db: Session,
    id: str,
    user: User,
):
    try:
        user_exist = db.execute(
            select(User).filter(User.id_user == id)
        ).scalar_one()
        if not user_exist:
            raise ValueError("User not found")
        user_exist.isact = False
        user_exist.updated_by = user.id
        db.add(user_exist)
        db.commit()
        db.refresh(user_exist)
        return user_exist
    except Exception as e:
        print("Error delete user \n", e)
        raise ValueError("Failed delete user")
# async def list_user(
#     db: Session,
#     page: int,
#     page_size: int,
#     src: Optional[str] = None
# ):
#     try:        
#         limit = page_size
#         offset = (page - 1) * limit

#         query = (select(User).filter(User.isact==True)
#         )
#         query_count = (select(func.count(User.id)).filter(User.isact==True)
#         )

#         if src:
#             query = (query
#                      .filter(User.name.ilike(f"%{src}%"))
#                      .filter(User.email.ilike(f"%{src}%"))
#                      )
#             query_count = (query_count
#                      .filter(User.name.ilike(f"%{src}%"))
#                      .filter(User.email.ilike(f"%{src}%"))
#                      )

#         query = (
#             query.order_by(User.created_at.desc())
#             .limit(limit=limit)
#             .offset(offset=offset)
#         )

#         data = db.execute(query).scalars().all()
#         num_data = db.execute(query_count).scalar()
#         num_page = ceil(num_data / limit)
#         return (await formating_user(data), num_data, num_page)
#     except Exception as e:
#         raise ValueError(e)
async def list_user(
    db: Session,
    page: int,
    page_size: int,
    src: Optional[str] = None
):
    try:
        limit = page_size
        offset = (page - 1) * limit

        # Gunakan alias untuk tabel Client agar lebih fleksibel
        ClientAlias = aliased(Client)

        # Query utama dengan JOIN ke Client
        query = (select(User)
                 .outerjoin(ClientAlias, ClientAlias.id == User.client_id)
                 .filter(User.isact == True))

        # Query count untuk paginasi
        query_count = (select(func.count(User.id))
                    .outerjoin(ClientAlias, ClientAlias.id == User.client_id)
                    .filter(User.isact == True))

        # Jika ada pencarian (src), cari di nama user & nama client
        if src:
            query = (query.filter(
                (User.name.ilike(f"%{src}%")) |
                (User.email.ilike(f"%{src}%")) |
                (ClientAlias.name.ilike(f"%{src}%"))
            ))

            query_count = (query_count.filter(
                (User.name.ilike(f"%{src}%")) |
                (User.email.ilike(f"%{src}%")) |
                (ClientAlias.name.ilike(f"%{src}%"))
            ))

        # Tambahkan order, limit, dan offset
        query = (query.order_by(User.created_at.desc())
                 .limit(limit)
                 .offset(offset))

        # Eksekusi query
        data = db.execute(query).scalars().all()
        num_data = db.execute(query_count).scalar()
        num_page = ceil(num_data / limit)

        return (await formating_user(data), num_data, num_page)

    except Exception as e:
        raise ValueError(e)
    
async def formating_user(data):
    ls_data = []
    for d in data:
        ls_data.append({
            "id_user": d.id_user,
            "name": d.name,
            "email": d.email,
            "phone": d.phone,
            "address": d.address,
            "client": {
                "id": d.client_user.id if d.client_user else None,
                "name": d.client_user.name if d.client_user else None,
            },
            "role": {
                "id": d.roles[0].id if d.roles else None,
                "name": d.roles[0].name if d.roles else None,
                "name": d.roles[0].name if d.roles else None,
            },
            "status": d.isact,
        })
    return ls_data