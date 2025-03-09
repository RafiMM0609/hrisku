from typing import Optional
import secrets
from sqlalchemy import select, func
from sqlalchemy.orm import Session
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
    db:Session
):
    try:
        data = db.execute(
            select(
                Role.id, Role.name, Role)
        ).scalars().all()
    except Exception as e:
        raise ValueError(e)