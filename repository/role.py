from typing import Optional
from math import ceil
import secrets
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local
from models.User import User
from models.Role import Role
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.user_management import AddUserRequest
import os
import asyncio


async def list_role(
    db:Session,
    page_size:int,
    page:int,
):
    try:
        limit = page_size
        offset = (page - 1) * limit
        query = (select(
            Role.id, Role.name, Role.users)
        ).options(selectinload(Role.users), selectinload(Role.permissions))
        # data = db.execute(query).scalars().all()
        data = db.execute(query).mappings().all()
        query_count = (select(func.count(Role.id))
        )
        query = (
            query.order_by(Role.created_at.desc())
            .limit(limit=limit)
            .offset(offset=offset)
        )
        num_data = db.execute(query_count).scalar()
        num_page = ceil(num_data / limit)
        return (await formating_role(data), num_data, num_page)
    except Exception as e:
        raise ValueError(e)

async def formating_role(data):
    print("ini data hasil query: \n", data)
    data_response = []
    for d in data:
        print("ini data role : \n", d)
        print("ini data role permission : \n", d.permissions)
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
            "total_user": len(data.users),
            "permission": formated_permission,
            "status": d.isact
            }
        )
    return data_response

    
    