from typing import Optional, List
import secrets
from math import ceil
from sqlalchemy import select, func
from sqlalchemy.orm import Session, aliased, joinedload
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, delete_file_in_local, generate_link_download
from models.User import User
from models.Role import Role
from models.Client import Client
from models.Contract import Contract
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
    DataOutlet,
    ContractManagement,
    DataContractManagement,
    HistoryContract,
    ClientData,
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
        # Get user with optional client and outlet relationship
        query = select(
            User, 
            Client, 
            ClientOutlet
        ).outerjoin(
            Client, User.client_id == Client.id
        ).outerjoin(
            ClientOutlet, User.outlet_id == ClientOutlet.id
        ).filter(
            User.id_user == talent_id,
            User.isact == True
        ).limit(1)
        
        result = db.execute(query).first()
        
        if not result:
            raise ValueError("Talent not found")
        
        user, client, outlet = result
        
        # Get shift information
        shift_query = select(ShiftSchedule).filter(
            ShiftSchedule.emp_id == user.id,
            ShiftSchedule.isact == True
        )
        shifts = db.execute(shift_query).scalars().all()
        
        # Format shift data according to DataWorkingArrangement model
        work_arrangements = []
        for shift in shifts:
            work_arr = DataWorkingArrangement(
                shift_id=shift.id_shift or "S001",
                day=shift.day or "Monday",
                time_start=shift.time_start.strftime("%H:%M") if shift.time_start else "08:00",
                time_end=shift.time_end.strftime("%H:%M") if shift.time_end else "15:00"
            )
            work_arrangements.append(work_arr)
        
        # If no shifts found, add a default one to match model requirements
        if not work_arrangements:
            work_arrangements.append(DataWorkingArrangement())
        
        # Create output using the proper pydantic models
        client_org = ClientData(
            id=client.id_client if client else None,
            name=client.name if client else None,
            address=client.address if client else None
        ) if client else None
        
        outlet_data = DataOutlet(
            name=outlet.name if outlet else None,
            address=outlet.address if outlet else None,
            latitude=float(outlet.latitude) if outlet and outlet.latitude else None,
            longitude=float(outlet.longitude) if outlet and outlet.longitude else None
        ) if outlet else None
        
        return TalentMapping(
            client=client_org,
            outlet=outlet_data,
            workdays=len(work_arrangements) if work_arrangements else 5,
            workarr=work_arrangements
        ).dict()
        
    except Exception as e:
        print(f"Error getting talent mapping: {e}")
        raise ValueError(f"Failed to get talent mapping")

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
    ).dict()

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

async def get_contract_management(db: Session, talent_id: str) -> ContractManagement:
    """
    Get contract management data for a specific talent_id.
    """
    try:
        user = db.execute(
            select(User)
            .options(
                joinedload(User.roles),
                joinedload(User.contract_user)
            )
            .filter(User.id_user == talent_id, User.isact == True)
        ).unique().scalar_one_or_none()

        if not user:
            raise ValueError("Talent not found")

        # Extract role name
        role_name = user.roles[0].name if user.roles else None

        # Extract active contract (most recent)
        active_contract = None
        if user.contract_user:
            active_contract = max(
                user.contract_user,
                key=lambda c: c.created_at,
                default=None
            )

        # Format active contract data
        active_contract_data = DataContractManagement(
            id=active_contract.id,
            start_date=active_contract.start.strftime("%d-%m-%Y") if active_contract and active_contract.start else None,
            end_date=active_contract.end.strftime("%d-%m-%Y") if active_contract and active_contract.end else None,
            file=generate_link_download(active_contract.file) if active_contract and active_contract.file else None
        ) if active_contract else None

        # Format contract history
        history_data = [
            HistoryContract(
                start_date=contract.start.strftime("%d-%m-%Y") if contract.start else None,
                end_date=contract.end.strftime("%d-%m-%Y") if contract.end else None,
                file=generate_link_download(contract.file) if contract.file else None,
                file_name=contract.file_name
            )
            for contract in sorted(user.contract_user, key=lambda c: c.created_at, reverse=True)
        ]

        # Return ContractManagement model
        return ContractManagement(
            talent_id=user.id_user,
            talent_name=user.name,
            talent_role=role_name,
            contract=active_contract_data,
            history=history_data
        ).dict()
    except Exception as e:
        print(f"Error getting contract management: {e}")
        raise ValueError("Failed to get contract management data")