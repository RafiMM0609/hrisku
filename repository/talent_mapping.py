from typing import Optional, List
import secrets
from math import ceil
from sqlalchemy import or_, select, func, update
from sqlalchemy.orm import Session, aliased
from core.security import validated_user_password, generate_hash_password
from core.file import upload_file_to_local, upload_file_from_path_to_minio, generate_link_download
from core.mail import send_first_password_email
from models.User import User
from models.Role import Role
from models.UserRole import UserRole
from models.ShiftSchedule import ShiftSchedule
from models.Client import Client
from models.ClientOutlet import ClientOutlet
from models import SessionLocal
from datetime import datetime, timedelta
from pytz import timezone
from models.Contract import Contract
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.talent_mapping import (
    ListAllUser,
    RegisTalentRequest,
    EditTalentRequest,
    ShiftEdit,
    ContractManagement,
    DetailTalentMapping,
    Organization, 
    ShiftResponse, 
    DataContractManagement, 
    HistoryContract,
    ViewTalent,
    ViewPersonalInformation,
    ViewMappingInformation,
    EditContractManagement,
    DataCalenderWorkarr,
)
import os
import asyncio
from repository.payroll import add_monthly_salary_emp, generate_file_excel
from repository.attendancesummary import create_update_attendance_summary
from fastapi.logger import logger  # Add logger for better debugging

async def get_menu_calender(
    db: Session,
    client_id: Optional[str],
    outlet_id: Optional[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[DataCalenderWorkarr]:
    try:
        if not client_id or not outlet_id:
            raise ValueError("Client ID and Outlet ID must be provided")

        this_year = datetime.now().year
        start_date = start_date or datetime.now().strftime("%Y-%m-%d")
        end_date = end_date or (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d")
        
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        query = (
            select(ShiftSchedule)
            .filter(
                ShiftSchedule.client_id == client_id,
                ShiftSchedule.outlet_id == outlet_id,
                ShiftSchedule.isact == True,
                func.extract('year', ShiftSchedule.created_at) == this_year
            )
        )
        data_shift = db.execute(query).scalars().all()

        if not data_shift:
            logger.warning(f"No shift schedules found for client_id={client_id}, outlet_id={outlet_id}")
            return []

        # Map the query results to the DataCalenderWorkarr Pydantic model
        result = []
        # Count workdays
        workdays = len(data_shift) if data_shift else 0
        for shift in data_shift:
            current_date = start_date_obj
            while current_date <= end_date_obj:
                if current_date.strftime("%A") == shift.day:  # Match day name
                    start_datetime = datetime.combine(current_date, shift.time_start)
                    end_datetime = datetime.combine(current_date, shift.time_end)
                    result.append(
                        DataCalenderWorkarr(
                            id=shift.id,
                            emp_id=shift.emp_id,
                            emp_name=shift.users.name,
                            client_id=shift.client_id,
                            outlet_id=shift.outlet_id,
                            day=shift.day,
                            time_start=start_datetime.strftime("%Y-%m-%d %H:%M"),
                            time_end=end_datetime.strftime("%Y-%m-%d %H:%M"),
                            workdays=workdays,
                            created_at=shift.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        ).dict()
                    )
                current_date += timedelta(days=1)

        return result

    except Exception as e:
        logger.error(f"Error in get_menu_calender: {e}")
        raise ValueError("Failed to get menu calendar")

async def map_shift_to_calendar(emp_id: str, start_time: str, end_time: str, day: str, db: Session):
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")
        day_mapping = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }
        day_index = day_mapping.get(day)
        if day_index is None:
            raise ValueError("Invalid day provided")

        # Assuming start date is today for example purposes
        start_date = datetime.now()
        while start_date.weekday() != day_index:
            start_date += timedelta(days=1)

        shifts = []
        for i in range(10):  # Generate shifts for the next 10 occurrences
            shift_start = start_date.replace(hour=start.hour, minute=start.minute)
            shift_end = start_date.replace(hour=end.hour, minute=end.minute)
            shifts.append({
                "id": emp_id,
                "title": "Shift",
                "start": shift_start.strftime("%Y-%m-%d %H:%M"),
                "end": shift_end.strftime("%Y-%m-%d %H:%M"),
                "day": day
            })
            start_date += timedelta(days=7)

        return shifts

    except Exception as e:
        print(f"Error mapping shift to calendar: {e}")
        raise ValueError("Failed to map shift to calendar")

async def delete_talent(db: Session, user:User, talent_id: str):
    try:
        exist_data = db.execute(
            select(User).filter(User.id_user == talent_id)
        ).scalar_one_or_none()
        if not exist_data:
            raise ValueError("User not found")
        exist_data.isact=False
        exist_data.updated_at=datetime.now(tz=timezone(TZ))
        exist_data.updated_by=user.id
        db.add(exist_data)
        db.commit()
        return "oke"
    except Exception as e:
        print("Error delete talent: \n", e)
        raise ValueError("Failed delete talent")
async def ViewTalentData(
    db: Session,
    talent_id: str
) -> ViewTalent:
    try:
        # Query to fetch user and related client and outlet information
        query = select(
            User.id,
            User.id_user,
            User.name,
            User.birth_date,
            User.nik,
            User.email,
            User.phone,
            User.address,
            User.photo,
            User.face_id,
            Role.id.label('role_id'),
            Role.name.label('role_name'),
            Client.id_client.label('client_id'),
            Client.name.label('client_name'),
            Client.address.label('client_address'),
            ClientOutlet.name.label('outlet_name'),
            ClientOutlet.address.label('outlet_address'),
            ClientOutlet.latitude.label('outlet_latitude'),
            ClientOutlet.longitude.label('outlet_longitude')
        ).outerjoin(
            Client, User.client_id == Client.id
        ).outerjoin(
            ClientOutlet, User.outlet_id == ClientOutlet.id
        ).outerjoin(
            UserRole, User.id == UserRole.c.emp_id
        ).outerjoin(
            Role, UserRole.c.role_id == Role.id
        ).filter(
            User.id_user == talent_id
        ).limit(1)

        data = db.execute(query).one_or_none()

        if not data:
            return ViewTalent(
                personal=ViewPersonalInformation(
                    talent_id=None,
                    name=None,
                    role_name=None,
                    dob=None,
                    nik=None,
                    email=None,
                    phone=None,
                    address=None,
                    face_id=None,
                    photo=None,
                ),
                mapping=ViewMappingInformation(
                    client_id=None,
                    client_name=None,
                    client_address=None,
                    outlet_name=None,
                    outlet_address=None,
                    outlet_latitude=None,
                    outlet_longitude=None,
                    workdays=None,
                    workarg=[],
                    contract=None
                )
            ).dict()

        # Query to fetch user shift information
        shift_query = select(
            ShiftSchedule.id_shift,
            ShiftSchedule.day,
            ShiftSchedule.time_start,
            ShiftSchedule.time_end,
            ShiftSchedule.workdays
        ).filter(
            ShiftSchedule.emp_id == data.id,  # Adjusted to use data.id
            ShiftSchedule.isact == True
        )

        shifts = db.execute(shift_query).all()
        # Calculate workdays as the number of active shifts
        workdays = len(shifts) if shifts else 0

        shift_responses = [
            ShiftResponse(
                shift_id=shift.id_shift,
                day=shift.day,
                start_time=shift.time_start.strftime("%H:%M"),
                end_time=shift.time_end.strftime("%H:%M")
            ) for shift in shifts
        ]

        # Query to fetch contract information
        contract_query = select(
            Contract.start,
            Contract.end,
            Contract.file
        ).filter(
            Contract.emp_id == data.id,  # Adjusted to use data.id
            Contract.isact == True
        ).limit(1)

        contract_data = db.execute(contract_query).one_or_none()
        contract_management = None
        if contract_data:
            contract_management = ContractManagement(
                start_date=contract_data.start.strftime("%d-%m-%Y") if contract_data.start else None,
                end_date=contract_data.end.strftime("%d-%m-%Y") if contract_data.end else None,
                file=generate_link_download(contract_data.file) if contract_data.file else None,
            )

        personal_info = ViewPersonalInformation(
            talent_id=data.id_user,
            name=data.name,
            role_name=data.role_name,
            dob=data.birth_date.strftime("%d-%m-%Y") if data.birth_date else None,
            nik=data.nik,
            email=data.email,
            phone=data.phone,
            address=data.address,
            face_id=generate_link_download(data.face_id) if data.face_id else None,
            photo=generate_link_download(data.photo) if data.photo else None
        )

        mapping_info = ViewMappingInformation(
            client_id=data.client_id,
            client_name=data.client_name,
            client_address=data.client_address,
            outlet_name=data.outlet_name,
            outlet_address=data.outlet_address,
            outlet_latitude=data.outlet_latitude,
            outlet_longitude=data.outlet_longitude,
            workdays=workdays,
            workarg=shift_responses,
            contract=contract_management
        )

        return ViewTalent(
            personal=personal_info,
            mapping=mapping_info
        ).dict()

    except Exception as e:
        print(f"Error retrieving talent data: {e}")
        raise ValueError("Failed to retrieve talent data")
        
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
        # If change photo
        if payload.photo:
            photo_path = os.path.join("profile", payload.photo.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=photo_path, local_path=payload.photo)
            print(photo_path)
        else:
            photo_path = None
        role = db.execute(
            select(Role)
            .filter(Role.id==role_id)).scalar()
        password = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        new_user = User(
            photo=photo_path,
            name=payload.name,
            birth_date=datetime.strptime(payload.dob, "%d-%m-%Y").date(),
            nik=payload.nik,
            outlet_id=payload.outlet_id,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            client_id=payload.client_id,
            first_login=password,
            created_by=user.id,
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
            background_tasks.add_task(
                add_mapping_schedule,
                new_user.client_id,
                new_user.id, 
                payload.shift, 
                payload.workdays,
                new_user.outlet_id
            )
        if isinstance(payload.contract, (list, tuple)):
            background_tasks.add_task(
                add_contract,
                new_user.id,
                payload.contract
            )
        await send_first_password_email(
            email_to=new_user.email,
            body={
                "email": new_user.email,
                "password": password
                }
        )
    except Exception as e:
        # Set all existing users with the same ID to inactive
        db.execute(
        update(User).where(User.id == new_user.id).values(isact=False)
        )
        db.commit()
        print("Error regis talent : \n", e)
        raise ValueError("Failed regis talent")

async def add_contract(emp_id: str, payload: ContractManagement):
    """
    Insert contract data for a talent into the Contract table.
    
    Args:
        db (Session): Database session
        emp_id (str): Talent ID
        payload (ContractManagement): Contract details
    """
    db = SessionLocal()  # Ambil koneksi dari pool
    try:            
        # Parse dates
        start_date = datetime.strptime(payload.start_date, "%d-%m-%Y").date()
        end_date = datetime.strptime(payload.end_date, "%d-%m-%Y").date()
        
        # Calculate period in months (approximate)
        delta = end_date - start_date
        # Simply get the year from the end date
        period = end_date.year
        
        # handle file contract
        if payload.file:
            file_path = os.path.join("contract", payload.file.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=file_path, local_path=payload.file)
        else:
            file_path = None

        new_contract = Contract(
            emp_id=emp_id,
            start=start_date,
            end=end_date,
            period=int(period),
            file=file_path,
            file_name=payload.file.split("-")[0],
            created_at=datetime.now(tz=timezone(TZ)),
            isact=True
        )
        
        db.add(new_contract)
        db.commit()
        
        return "oke"
        
    except Exception as e:
        db.rollback()
        print(f"Error adding contract: {e}")
        raise ValueError(f"Failed to add contract")
    finally:
        db.close()  # Jangan lupa close agar tidak bocor

async def add_mapping_schedule(client_id, emp_id, shift, workdays, outlet_id):
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
                outlet_id=outlet_id,
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


async def mapping_schedule_bak(db, client_id, emp_id, data, workdays):
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
    user: User,
    background_tasks: any,
    payload: EditTalentRequest,
    role_id: int = 1,
):
    try:
        # Retrieve the existing user
        user_exist = db.execute(
            select(User).filter(User.id_user == id_user).limit(1)
        ).scalar()

        if not user_exist:
            raise ValueError("User not found")

        # If changing photo
        if payload.photo:
            photo_path = os.path.join("profile", payload.photo.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=photo_path, local_path=payload.photo)
            print(photo_path)
            user_exist.photo = photo_path

        # Old email
        old_email = user_exist.email

        # Update fields only if payload values are not None
        if payload.name is not None:
            user_exist.name = payload.name
        if payload.dob is not None:
            user_exist.birth_date = datetime.strptime(payload.dob, "%d-%m-%Y").date()
        if payload.nik is not None:
            user_exist.nik = payload.nik
        if payload.outlet_id is not None:
            user_exist.outlet_id = payload.outlet_id
        if payload.email is not None:
            user_exist.email = payload.email
        if payload.phone is not None:
            user_exist.phone = payload.phone
        if payload.address is not None:
            user_exist.address = payload.address
        if payload.client_id is not None:
            user_exist.client_id = payload.client_id

        user_exist.updated_by = user.id
        db.add(user_exist)
        db.commit()
        db.refresh(user_exist)

        # # Handle email change and first login password
        # new_email = user_exist.email
        # if old_email != new_email and user_exist.first_login is not None:
        #     await send_first_password_email(
        #         email_to=user_exist.email,
        #         body={
        #             "email": user_exist.email,
        #             "password": user_exist.first_login,
        #         }
        #     )

        # Handle email change and first login password
        new_email = user_exist.email
        if old_email != new_email and user_exist.first_login is not None:
            background_tasks.add_task(
                send_first_password_email,
                email_to=user_exist.email,
                body={
                    "email": user_exist.email,
                    "password": user_exist.first_login,
                }
            )

        # Handle shifts and contracts in background tasks
        if isinstance(payload.shift, (list, tuple)):
            background_tasks.add_task(
                edit_schedule,
                user_exist.client_id,
                user_exist.id,
                payload.shift,
                payload.workdays,
                user.id,
                user_exist.outlet_id,
            )
        if payload.contract:
            background_tasks.add_task(
                edit_contract,
                user.id,
                user_exist.id,
                payload.contract,
            )

        # Add monthly salary task
        data_monthly_salary = {
            "emp_id": user_exist.id,
            "client_id": user_exist.client_id,
        }
        background_tasks.add_task(
            add_monthly_salary_emp,
            **data_monthly_salary
        )
        background_tasks.add_task(
            generate_file_excel,
            **data_monthly_salary
        )

        # Add attendance summary task
        background_tasks.add_task(
            create_update_attendance_summary,
            **data_monthly_salary
        )

    except Exception as e:
        print("Error editing talent: \n", e)
        raise ValueError("Failed to edit talent")

async def edit_contract(user_id: str, emp_id: str, payload: EditContractManagement):
    """
    Edit contract if payload.id is available, otherwise create a new one.
    """
    db = SessionLocal()  # Get connection from the pool
    try:
        # Parse dates
        start_date = datetime.strptime(payload.start_date, "%d-%m-%Y").date()
        end_date = datetime.strptime(payload.end_date, "%d-%m-%Y").date()
        
        # Calculate period in months (approximate)
        period = end_date.year  # Simply get the year from the end date

        # handle file contract
        if payload.file:
            file_path = os.path.join("contract", payload.file.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=file_path, local_path=payload.file)
        else:
            file_path = None
        
        if payload.id:
            # Fetch the existing contract
            contract_query = select(Contract).filter(
                Contract.id == payload.id,
                Contract.emp_id == emp_id,
                Contract.isact == True
            ).limit(1)
            existing_contract = db.execute(contract_query).scalar_one_or_none()
            
            if not existing_contract:
                raise ValueError("Contract not found for the given employee ID")
            
            # Update contract details
            existing_contract.start = start_date
            existing_contract.end = end_date
            existing_contract.period = int(period)
            existing_contract.file = file_path
            existing_contract.file_name = payload.file.split("/")[-1] if payload.file else None
            existing_contract.updated_at = datetime.now(tz=timezone(TZ))
            existing_contract.updated_by = user_id
        else:
            # Create a new contract
            new_contract = Contract(
                emp_id=emp_id,
                start=start_date,
                end=end_date,
                period=int(period),
                file=file_path,
                file_name=payload.file.split("/")[-1] if payload.file else None,
                created_at=datetime.now(tz=timezone(TZ)),
                updated_by=user_id,
                isact=True
            )
            db.add(new_contract)
        
        db.commit()
        return "Contract updated successfully" if payload.id else "Contract created successfully"
        
    except Exception as e:
        db.rollback()
        print(f"Error editing/creating contract: {e}")
        raise ValueError("Failed to edit or create contract", e)
    finally:
        db.close()  # Ensure the connection is closed

async def edit_schedule(client_id, emp_id, shift:List[ShiftEdit], workdays, user_id, outlet_id):
    db = SessionLocal()  # Ambil koneksi dari pool
    db.execute(
        update(ShiftSchedule)
        .where(ShiftSchedule.emp_id==emp_id)
        .values(isact=False)
    )
    db.commit()
    try:
        for d in shift:
            if d.id_shift == None:
                # Check if sfhit in the same day exist
                query_check = (
                    select(ShiftSchedule.id)
                    .filter(ShiftSchedule.isact==True)
                    .filter(ShiftSchedule.emp_id==emp_id)
                    .filter(ShiftSchedule.day==d.day)
                    .limit(1)
                )
                exist_shift_same_day = db.execute(
                    query_check
                ).scalar()
                if exist_shift_same_day:
                    print("You have inputed the same day shift")
                    continue  # Skip creating a new shift for this day
                # Create a new shift schedule
                new_shift= ShiftSchedule(
                    emp_id=emp_id,
                    client_id=client_id,
                    workdays=workdays,
                    time_start=datetime.strptime(d.start_time, "%H:%M").time(),
                    time_end=datetime.strptime(d.end_time, "%H:%M").time(),
                    day=d.day,
                    created_at=datetime.now(tz=timezone(TZ)),
                    outlet_id=outlet_id,
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
            else: 
                exist_data = db.execute(
                    select(ShiftSchedule)
                    .filter(ShiftSchedule.id_shift==d.id_shift)
                ).scalar()
                exist_data.updated_by=user_id
                exist_data.isact=True
                exist_data.day=d.day
                exist_data.time_start=d.start_time
                exist_data.time_end=d.end_time

        return "oke"                
    except Exception as e:
        print("Error edit outlet: \n", e)

async def list_talent(
    db: Session,
    page: int,
    page_size: int,
    src: Optional[str] = None,
    user: Optional[User] = None,
)->ListAllUser:
    try:
        limit = page_size
        offset = (page - 1) * limit

        # Query utama dengan JOIN ke Client dan UserRole
        query = (select(
            User.id_user,
            User.name,
            User.birth_date,
            User.nik,
            User.email,
            User.phone,
            User.address,
            User.isact,
            User.photo
            )
            .join(UserRole, User.id == UserRole.c.emp_id)
            .filter(User.isact == True, UserRole.c.role_id == 1))


        # Query count untuk paginasi
        query_count = (select(func.count(User.id))
                       .join(UserRole, User.id == UserRole.c.emp_id)
                       .filter(User.isact == True, UserRole.c.role_id == 1))

        # If admin hanya client dia
        if user:
            if user.roles[0].id==2:
                query = query.filter(or_(User.client_id == user.client_id))
                query_count = query_count.filter(or_(User.client_id == user.client_id))
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
            "photo": generate_link_download(d.photo),
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
) -> DetailTalentMapping:
    try:
        query = select(User).filter(User.id_user == id_user).limit(1)
        data = db.execute(query).scalar_one_or_none()
        
        if not data:
            raise ValueError("User not found")
    
        return await formating_detail(data)
    
    except Exception as e:
        print("Error detail mapping: \n", e)
        raise ValueError("Failed to get data")

async def formating_detail(data: User) -> DetailTalentMapping:
    contract_data = None
    if data.contract_user:
        contract = data.contract_user[0]  # Assuming the first contract is the current one
        history = [
            HistoryContract(
                start_date=h.start.strftime("%d-%m-%Y") if h.start else None,
                end_date=h.end.strftime("%d-%m-%Y") if h.end else None,
                file=generate_link_download(h.file) if h.file else None,
                file_name=h.file_name
            ) for h in (data.contract_user or [])
        ]
        contract_data = DataContractManagement(
            id=contract.id,
            start_date=contract.start.strftime("%d-%m-%Y") if contract.start else None,
            end_date=contract.end.strftime("%d-%m-%Y") if contract.end else None,
            file=generate_link_download(contract.file),
            history=history
        )

    # Count workdays from user_shift
    workdays = len(data.user_shift) if data.user_shift else 0
    return DetailTalentMapping(
        talent_id=data.id_user,
        photo=data.photo,
        name=data.name,
        dob=data.birth_date.strftime("%d-%m-%Y") if data.birth_date else None,
        nik=data.nik,
        email=data.email,
        phone=data.phone,
        address=data.address,
        client=Organization(
            id=data.client_user.id,
            name=data.client_user.name
        ) if data.client_user else None,
        outlet=Organization(
            id=data.user_outlet.id,
            name=data.user_outlet.name
        ) if data.user_outlet else None,
        workdays=workdays,
        shift=[
            ShiftResponse(
                shift_id=x.id_shift,
                day=x.day,
                start_time=x.time_start.strftime("%H:%M"),
                end_time=x.time_end.strftime("%H:%M")
            ) for x in (data.user_shift or []) if x.isact
        ],
        contract=contract_data
    ).dict()

async def get_contract_history(
    db: Session,
    talent_id: str,
) -> List[HistoryContract]:
    try:
        emp_id = db.execute(
            select(User.id).filter(User.id_user == talent_id)
        ).scalar_one_or_none()
        if not emp_id:
            return []
        query = select(Contract).filter(Contract.emp_id == emp_id, Contract.isact == True)
        data = db.execute(query).scalars().all()
        if not data:
            return []

        return [
            HistoryContract(
                start_date=d.start.strftime("%d-%m-%Y") if d.start else None,
                end_date=d.end.strftime("%d-%m-%Y") if d.end else None,
                file=generate_link_download(d.file) if d.file else None,
                file_name=d.file_name
            ).dict() for d in data
        ]
    except Exception as e:
        print("Error retrieving contract history: \n", e)
        raise ValueError("Failed to retrieve contract history")