from typing import Optional
from math import ceil
import secrets
from sqlalchemy import select, func, distinct, update
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


async def delete_client(
    id:int,
    db:Session,
    user=User,
):
    try:
        client = db.execute(select(Client).filter(Client.id_client == id)).scalar()
        if not client:
            raise ValueError("Client not found")
        client.isact = False
        client.updated_by = user.id
        db.add(client)
        db.commit()
        return "oke"
    except Exception as e:
        db.rollback()
        print("Error delete client", e)
        raise ValueError("Failed delete client")
async def add_client(
    db:Session,
    user:User,
    payload:AddClientRequest,
)->Client:
    try:
        due_date_payment = datetime.strptime(payload.payment_date, "%d-%m-%Y").date()
        new_client = Client(
            name=payload.name,
            address=payload.address,
            fee_agency=payload.agency_fee,
            due_date_payment=due_date_payment,
            cs_person=payload.cs_person,
            cs_number=payload.cs_number,
            cs_email=payload.cs_email,
            basic_salary=payload.basic_salary,
            created_at=datetime.now(tz=timezone(TZ)),
        )
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        exist_client_id = new_client.id
        # new_client.id_client = await create_custom_id(new_client.id)
        # db.merge(new_client)
        # db.commit()
        db.execute(
        update(Client).where(Client.id == new_client.id).values(id_client=await create_custom_id(new_client.id))
        )
        db.commit()
        ls_bpjs = []
        ls_allowances = []
        ls_outlet = []
        for data in payload.outlet:
            new_outlet = ClientOutlet(
                client_id = new_client.id,
                name = data.name,
                longitude = data.longitude,
                latitude = data.latitude,
                address = data.address
            )
            ls_outlet.append(new_outlet)
        if isinstance(payload.bpjs, (list, tuple)):
            for data in payload.bpjs:
                new_bpjs = Bpjs(
                    client_id = new_client.id,
                    name = data.name,
                    amount = data.amount
                )
                ls_bpjs.append(new_bpjs)
        if isinstance(payload.allowences, (list, tuple)):
            for data in payload.allowences:
                new_allowances = Allowances(
                    client_id = new_client.id,
                    name = data.name,
                    amount = data.amount
                )
                ls_allowances.append(new_allowances)
        # with Session(engine) as session:
        db.bulk_save_objects(ls_bpjs)
        db.bulk_save_objects(ls_allowances)
        db.bulk_save_objects(ls_outlet)
        db.commit()
        return new_client
    except Exception as e:
        db.execute(
            (
                update(Client)
                .where(Client.id == exist_client_id)
                .values(isact=False)
            )
        )
        db.commit()
        raise ValueError(e)
async def create_custom_id(
        id: int, 
        prefix:Optional[str]="C"
) -> str:
    num_digits = len(str(id))
    formatted_id = f"{id:0{num_digits+1}d}"  
    return prefix + formatted_id
async def add_validator(db: Session, payload: AddClientRequest):
    try:
        errors = None
        queries = []

        if payload.name:
            queries.append(select(Client.id).filter(Client.name == payload.name, Client.isact==True).exists())

        if payload.cs_email:
            queries.append(select(Client.cs_email).filter(Client.cs_email == payload.cs_email, Client.isact==True).exists())

        if payload.cs_number:
            queries.append(select(Client.cs_number).filter(Client.cs_number == payload.cs_number, Client.isact==True).exists())

        if queries:
            result = db.execute(select(*queries)).fetchall()

            if payload.name and result[0][0]:
                errors = "Name already exist"
            if payload.cs_email and result[0][1]:
                errors = "CS Email already used"
            if payload.cs_number and result[0][2]:
                errors = "CS Phone number already used"
        if errors:
            return {"success": False, "errors": errors}
        return {"success": True}

    except Exception as e:
        print(f"Validation error: {e}")

async def edit_validator(db: Session, payload: AddClientRequest, id:int):
    try:
        errors = None
        queries = []
        # For client checking
        # if payload.role_id:
        #     queries.append(select(Client.id).filter(Client.id == payload.role_id).exists())

        if payload.name:
            queries.append(select(Client.id).filter(Client.id != id, Client.name == payload.name, Client.isact==True).exists())

        if payload.cs_email:
            queries.append(select(Client.cs_email).filter(Client.id != id, Client.cs_email == payload.cs_email, Client.isact==True).exists())

        if payload.cs_number:
            queries.append(select(Client.cs_number).filter(Client.id != id, Client.cs_number == payload.cs_email, Client.isact==True).exists())

        if queries:
            result = db.execute(select(*queries)).fetchall()

            if payload.role_id and result[0][0]:
                errors = "Name already exist"
            if payload.role_id and result[0][1]:
                errors = "CS Email already used"
            if payload.role_id and result[0][2]:
                errors = "CS Phone number already used"
        if errors:
            return {"success": False, "errors": errors}
        return {"success": True}

    except Exception as e:
        print(f"Validation error: {e}")

async def edit_client(
    db:Session,
    user:User,
    payload:EditClientRequest,
    client_id:int,
)->Client:
    try:
        client = db.execute(select(Client).filter(Client.id_client == client_id)).scalar()
        if not client:
            raise ValueError("Client not found")
        client.name = payload.name
        client.address = payload.address
        client.fee_agency = payload.agency_fee
        client.due_date_payment = payload.payment_date
        client.cs_person = payload.cs_person
        client.cs_number = payload.cs_number
        client.cs_email = payload.cs_email
        client.updated_by = user.id
        db.add(client)
        db.commit()
        ls_bpjs = []
        ls_allowances = []
        ls_outlet = []
        if isinstance(payload.outlet, (list, tuple)):
            db.execute(
                update(ClientOutlet)
                .where(ClientOutlet.client_id==client.id)
                .values(isact=False)
            )
            db.commit()
            for data in payload.outlet:
                new_outlet = ClientOutlet(
                    client_id = client.id,
                    name = data.name,
                    longitude = data.longitude,
                    latitude = data.latitude,
                    address = data.address
                )
                ls_outlet.append(new_outlet)
        if isinstance(payload.bpjs, (list, tuple)):
            db.execute(
                update(Bpjs)
                .where(Bpjs.client_id==client.id)
                .values(isact=False)
            )
            db.commit()
            for data in payload.bpjs:
                new_bpjs = Bpjs(
                    client_id = client.id,
                    name = data.name,
                    amount = data.amount
                )
                ls_bpjs.append(new_bpjs)
        if isinstance(payload.allowences, (list, tuple)):
            db.execute(
                update(Allowances)
                .where(Allowances.client_id==client.id)
                .values(isact=False)
            )
            db.commit()
            for data in payload.allowences:
                new_allowances = Allowances(
                    client_id = client.id,
                    name = data.name,
                    amount = data.amount
                )
                ls_allowances.append(new_allowances)
        db.bulk_save_objects(ls_bpjs)
        db.bulk_save_objects(ls_allowances)
        db.bulk_save_objects(ls_outlet)
        db.commit()    
        return "oke"
    except Exception as e:
        db.rollback()
        db.execute(
            update(Client)
            .where(Client.id==client.id)
            .values(isact=False)
        )
        db.commit()
        raise ValueError(e)
    
async def list_client(
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
            "id": item.id_client,
            "name": item.name,
            "address": item.address,
            "payment_date": str(item.due_date_payment),
            "outlet": [
                {
                    "id": d.id,
                    "name": d.name,
                    "address": d.address,
                    "created_at": d.created_at.astimezone(
                        timezone(TZ)
                    ).strftime("%d-%m-%Y %H:%M:%S") if d.created_at else None,
                    "isact": d.isact
                } for d in (item.outlets or [])
            ],
            "cs_person": item.cs_person,
            "cs_number": item.cs_number,
            "cs_email": item.cs_email,
            "created_at": item.created_at.astimezone(
                timezone(TZ)
            ).strftime("%d-%m-%Y %H:%M:%S") if item.created_at else None,
            "isact": item.isact
        })
    return result

async def detail_client(
    db:Session,
    id:int
):
    try:
        query = select(Client).filter(Client.id_client == id).limit(1)
        client = db.execute(query).scalar()
        return await formatin_detail(client)
    except Exception as e:
        print("Error detail: \n",e)
        raise ValueError("Failed get detail client")
async def formatin_detail(data:Client):
    obj = {
        "name": data.name,
        "address": data.address,
        "outlet":[
            {
            "id": x.id,
            "name": x.name,
        } for x in data.outlets
        ] if data.outlets else [],
        "basic_salary": data.basic_salary,
        "agency_fee": data.fee_agency,
        "payment_date": data.due_date_payment.strftime("%d-%m-%Y"),
        "bpjs":[
            {
            "id": x.id,
            "name": x.name,
            "amount":x.amount,
        } for x in data.bpjs
        ] if data.bpjs else [],
        "allowences":[
            {
            "id": x.id,
            "name": x.name,
            "amount": x.amount,
        } for x in data.allowances
        ] if data.allowances else [],
        "cs_person":data.cs_person,
        "cs_number":data.cs_number,
        "cs_email":data.cs_email
    }
    return obj