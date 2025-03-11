from typing import Optional
from math import ceil
import secrets
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local
from models.Role import Role
from models.Module import Module
from models.Client import Client
from models.User import User
from models.ClientOutlet import ClientOutlet
from models.Bpjs import Bpjs
from models.Allowances import Allowances
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
import os
import asyncio
from math import ceil
from schemas.client import (
    AddClientRequest,
    EditClientRequest
)

async def list_client_billing(
    db:Session,
    src:Optional[str]=None,
    page:Optional[int]=1,
    page_size:Optional[int]=10,
):
    try:        
        limit = page_size
        offset = (page - 1) * limit

        query = (select(Client).filter(Client.isact==True)
        )
        query_count = (select(func.count(Client.id)).filter(Client.isact==True)
        )

        if src:
            query = (query
                     .filter(Client.name.ilike(f"%{src}%"))
                     )
            query_count = (query_count
                     .filter(Client.name.ilike(f"%{src}%"))
                     )

        query = (
            query.order_by(Client.created_at.desc())
            .limit(limit=limit)
            .offset(offset=offset)
        )

        data = db.execute(query).scalars().all()
        num_data = db.execute(query_count).scalar()
        num_page = ceil(num_data / limit)
        return (await formating_client(data), num_data, num_page)
    except Exception as e:
        raise ValueError(e)
    
async def formating_client(data):
    if not data:
        return []

    result = []
    for item in data:
        result.append({
            "id": item.id,
            "name": item.name,
            "address": item.address,
            "created_at": item.created_at.astimezone(
            timezone(TZ)
            ).strftime("%d %m %Y %H:%M:%S") if item.created_at else None,
            "isact": item.isact,
            "payment_status": item.payment_status,
        })
    return result

    