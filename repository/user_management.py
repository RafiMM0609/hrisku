from typing import Optional, List
import secrets
from core.mail import send_first_password_email
from math import ceil
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session, aliased
from core.file import generate_link_download, upload_file_from_path_to_minio
from models.User import User
from models.Role import Role
from models.UserRole import UserRole
from models.Client import Client
from datetime import datetime
from pytz import timezone
from settings import TZ
from schemas.user_management import (
    AddUserRequest,
    EditUserRequest
)
import os


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
                User.photo
            ).filter(User.id_user == id_user, User.isact==True)
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
        "photo": generate_link_download(user[6]),
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
    """
    This function is used to add a user to the database
    and send an email to the user with a password.
    If payload.role == 2, then payload.client_id is required.
    """
    try:
        # Validate that client_id is provided if role_id == 2
        if payload.role_id == 2 and not payload.client_id:
            raise ValueError("Client ID is required when role_id is 2")

        role = db.execute(
            select(Role).filter(Role.id == payload.role_id)
        ).scalar_one()
        if not role:
            raise ValueError("Role not found")

        password = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))

        if payload.photo:
            photo_path = os.path.join("profile", payload.photo.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=photo_path, local_path=payload.photo)
            print(photo_path)
        else:
            photo_path = None

        new_user = User(
            email=payload.email,
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
            first_login=password,
            created_by=user.id,
            photo=photo_path,
            created_at=datetime.now(tz=timezone(TZ)),
            client_id=payload.client_id if payload.client_id else None
        )
        new_user.roles.append(role)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        db.execute(
            update(User).where(User.id == new_user.id).values(id_user=await create_custom_id(new_user.id_seq))
        )
        db.commit()

        await send_first_password_email(
            email_to=new_user.email,
            body={
                "email": new_user.email,
                "password": password
            }
        )
        return new_user

    except ValueError as ve:
        print("ValueError occurred:", ve)
        db.rollback()
        raise ve

    except Exception as e:
        print("Error adding user:\n", e)
        db.rollback()
        if 'new_user' in locals():
            db.execute(
                update(User)
                .where(User.id == new_user.id)
                .values(isact=False)
            )
            db.commit()
        raise ValueError("Failed to add user")
    
async def create_custom_id(
        id: int, 
        prefix:Optional[str]="T"
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
            queries.append(select(User.id).filter(User.email == payload.email,
                                                   User.isact==True
                                                ).exists())

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
            queries.append(select(User)
                .filter(User.id_user != id, User.email == payload.email, User.isact==True).exists())

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
async def edit_user(
    db: Session,
    payload: EditUserRequest,
    id: str,
    user: User
):
    try:
        user_exist = db.execute(
            select(User).filter(User.id_user == id)
        ).scalar()
        if not user_exist:
            raise ValueError("User not found")
        if payload.role_id:
            role = db.execute(
                select(Role).filter(Role.id == payload.role_id)
            ).scalar()
            if not role:
                raise ValueError("Role not found")
            user_exist.roles.clear()
            user_exist.roles.append(role)
        # If changes photo
        if payload.photo:
            photo_path = os.path.join("profile", payload.photo.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=photo_path, local_path=payload.photo)
            print(photo_path)
        else:
            photo_path = None
        user_exist.name = payload.name
        user_exist.email = payload.email
        user_exist.phone = payload.phone
        user_exist.address = payload.address
        user_exist.photo = photo_path
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
    
async def formating_user(data:List[User]):
    ls_data = []
    for d in data:
        ls_data.append({
            "id_user": d.id_user,
            "photo": generate_link_download(d.photo),
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

async def edit_status_user(
    db:Session,
    user:User,
    id_user:str
):
    try:
        exist_data = db.execute(
            select(User)
            .filter(User.id_user==id_user, User.isact==True)
            .limit(1)
        ).scalar()
        exist_data.status = not exist_data.status
        # db.execute(
        #     update(User)
        #     .where(User.id_user==id_user)
        #     .values(status=False, updated_by=user.id)
        # )
        db.add(exist_data)
        db.commit()
        return "oke"
    except Exception as e:
        print("Error edit status user: \n", e)
        raise ValueError("Failed edit status user")