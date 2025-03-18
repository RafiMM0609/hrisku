from typing import Optional
from math import ceil
import secrets
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session, aliased
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local
from models.User import User
from models.Role import Role
from models.Client import Client
from models.Permission import Permission
from models.UserRole import UserRole
from models.Module import Module
from models.RolePermission import RolePermission
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.user_management import AddUserRequest
import os
import asyncio


from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session
from math import ceil

async def role_option(
    db:Session,
    src:Optional[str] = None
):
    try:
        query = (select(Role.id, Role.name).filter(Role.isact==True)
        )
        if src:
            query = query.filter(Role.name.ilike(f"%{src}%"))
        data = db.execute(query).all()
        return (await formating_role_option(data))
    except Exception as e:
        raise ValueError(e)
    
async def formating_role_option(data):
    lst = []
    for d in data:
        lst.append(
            {
                "id": d.id,
                "name": d.name
            }
        )
    return lst

async def list_role(
    db:Session,
    page_size:int,
    page:int,
    src:Optional[str]=None,
    # role_id:Optional[int] = None,
):
    try:
        limit = page_size
        offset = (page - 1) * limit

        query = (select(Role).filter(Role.isact==True)
        )
        query_count = (select(func.count(Role.id)).filter(Role.isact==True)
        )

        if src:
            query = query.filter(Role.name.ilike(f"%{src}%"))
            query_count = query_count.filter(Role.name.ilike(f"%{src}%"))
        # if role_id:
        #     query = query.filter(Role.id==role_id)
        #     query_count = query_count.filter(Role.id==role_id)
        #Order and Pagination
        query = (
            query.order_by(Role.created_at.desc())
            .limit(limit=limit)
            .offset(offset=offset)
        )
        data = db.execute(query).scalars().all()
        num_data = db.execute(query_count).scalar()
        num_page = ceil(num_data / limit)
        return (await formating_role(data), num_data, num_page)
    except Exception as e:
        raise ValueError(e)

async def formating_role(data):
    data_response = []
    for d in data:
        permissions = []
        for permission in d.permissions:
            exists = [x for x in permissions if x == permission]
            if len(exists) == 0:
                permissions.append(permission)
        data_permission =  sorted(permissions, key=lambda d: d.id)
        formated_permission = [
            {
                "id": x.id,
                "permission": x.name,
                "module": {
                    "id": x.module.id,
                    "nama": x.module.name,
                }
                if x.module != None
                else None,
            } for x in data_permission
        ]
        data_response.append(
            {
            "id": d.id,
            "name":d.name,
            "total_user": len(d.users),
            "permission": formated_permission,
            "status": d.isact
            }
        )
    return data_response

async def detail_role(
    db:Session,
    id_role:int,
):
    try:
        role = db.execute(
            select(Role)
            .filter(Role.id==id_role, Role.isact==True)
            .limit(1)
        ).scalar()

        total_emp = db.execute(
            select(func.count(User.id))
            .join(UserRole, User.id == UserRole.c.emp_id)
            .filter(UserRole.c.role_id == id_role, User.isact == True)
        ).scalar()
        return await formating_detail_role(role, total_emp)
    except Exception as e:
        print("Error get detail role: \n", e)
        raise ValueError("Failed get data")

async def formating_detail_role(d, total_emp):
    permissions = []
    for permission in d.permissions:
        exists = [x for x in permissions if x == permission]
        if len(exists) == 0:
            permissions.append(permission)
        data_permission =  sorted(permissions, key=lambda d: d.id)
        formated_permission = [
            {
                "id": x.id,
                "permission": x.name,
                "module": {
                    "id": x.module.id,
                    "nama": x.module.name,
                }
                if x.module != None
                else None,
            } for x in data_permission
        ]
        obj = {
            "id_role": d.id,
            "role_name":d.name,
            "total_user": total_emp,
            "permission": formated_permission,
            }
    return obj
    
    
async def list_user(
    db: Session,
    id_role:int,
    page: int,
    page_size: int,
    src: Optional[str] = None
):
    try:
        limit = page_size
        offset = (page - 1) * limit

        # Gunakan alias untuk tabel Client agar lebih fleksibel
        ClientAlias = aliased(Client)

            # select(func.count(User.id))
            # .join(UserRole, User.id == UserRole.c.emp_id)
            # .filter(UserRole.c.role_id == id_role, User.isact == True)


        # Query utama dengan JOIN ke Client
        query = (select(User)
                .outerjoin(ClientAlias, ClientAlias.id == User.client_id)
                .join(UserRole, User.id == UserRole.c.emp_id)
                .filter(UserRole.c.role_id == id_role, User.isact == True)
                .filter(User.isact == True))

        # Query count untuk paginasi
        query_count = (select(func.count(User.id))
                .outerjoin(ClientAlias, ClientAlias.id == User.client_id)
                .join(UserRole, User.id == UserRole.c.emp_id)
                .filter(UserRole.c.role_id == id_role, User.isact == True)
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
        print("Error list user: \n", e)
        raise ValueError("Failed get data")
    
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
            "status": d.status,
        })
    return ls_data