from typing import Optional, List
from math import ceil
from sqlalchemy import select, func, update, or_
from sqlalchemy.orm import Session, subqueryload 
from core.file import upload_file_from_path_to_minio, generate_link_download
from models.Client import Client
from models.Tax import Tax
from models.User import User
from models.ClientOutlet import ClientOutlet
from models.Bpjs import Bpjs
from models.Allowances import Allowances
from models.ContractClient import ContractClient
from models import SessionLocal
from datetime import datetime
from pytz import timezone
from settings import TZ
from repository.clientbilling import add_client_payment
import os
from math import ceil
from schemas.client import (
    AddClientRequest,
    EditClientRequest,
    EditOutletRequest,
    DataDetailClientSignature,
    OutletList,
    PayrollClient,
    DetailClient,
    EditBpjsRequest,
    EditAllowencesRequest,
    DataClientOption,
)

async def get_client_options(
    db: Session,
    src: Optional[str] = None,
):
    """
    Get client options for dropdown lists or selection menus.
    Returns a list of clients with minimal information (id, id_client, name, address).
    """
    try:
        # Build base query
        query = select(Client).filter(Client.isact == True)

        # Apply search filter if provided
        if src:
            query = query.filter(Client.name.ilike(f"%{src}%"))

        # Apply pagination
        query = (
            query.order_by(Client.id.asc())
        )

        # Execute queries
        clients = db.execute(query).scalars().all()

        # Format the results
        result = []
        for client in clients:
            result.append(
                DataClientOption(
                    id=client.id,
                    id_client=client.id_client,
                    name=client.name,
                    address=client.address
                ).dict()
            )

        return result
    except Exception as e:
        print(f"Error fetching client options: {e}")
        raise ValueError("Failed to get client options")

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
    background_tasks:any,
)->Client:
    try:
        # if change photo
        if payload.photo:
            photo_path = os.path.join("client", payload.photo.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=photo_path, local_path=payload.photo)
            print(photo_path)
        else:
            photo_path = None
        due_date_payment = datetime.strptime(payload.payment_date, "%d-%m-%Y").date()
        new_client = Client(
            photo=photo_path,
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
        db.execute(
        update(Client).where(Client.id == new_client.id).values(id_client=await create_custom_id(new_client.id))
        )
        db.commit()
        ls_bpjs = []
        ls_allowances = []
        ls_outlet = []
        if isinstance(payload.outlet, (list, tuple)):
            background_tasks.add_task(
                add_outlet,
                payload.outlet,
                new_client.id
            )
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
        # Contract Handler
        if payload.start_contract:
            background_tasks.add_task(
                add_client_contract,
                payload=payload,
                client_id=new_client.id,
            )
        # Tax handler
        data_tax = {
            "id_client": new_client.id, 
            "user_id": user.id
        }
        background_tasks.add_task(
            add_tax_ppn,
            **data_tax
        )
        data_tax_pph = {
            "id_client": new_client.id, 
            "user_id": user.id, 
            "basic_salary": payload.basic_salary
        }
        background_tasks.add_task(
        add_tax_pph,
        **data_tax_pph
        )
        db.bulk_save_objects(ls_bpjs)
        db.bulk_save_objects(ls_allowances)
        db.bulk_save_objects(ls_outlet)
        db.commit()

        # Client payment handler
        background_tasks.add_task(
            add_client_payment,
            new_client.id,
        )        
        return new_client
    except Exception as e:
        raise ValueError(e)
    
async def add_client_contract(payload: AddClientRequest, client_id):
    """
    This function adds a client contract to the ContractClient table based on the AddClientRequest schema.
    Uses LocalSession to add data.
    """
    db = SessionLocal()
    try:
        # Dynamically assign client_id and other fields from payload
        new_client_contract = ContractClient(
            client_id=client_id,  # Integer, required
            start=datetime.strptime(payload.start_contract, "%d-%m-%Y").date() if payload.start_contract else None,  # Date
            end=datetime.strptime(payload.end_contract, "%d-%m-%Y").date() if payload.end_contract else None,  # Date
            file_contract=payload.file_contract,  # String (max length 255), optional
            created_at=datetime.now(tz=timezone(TZ)),  # DateTime with timezone
        )
        db.add(new_client_contract)
        db.commit()
        db.refresh(new_client_contract)
        return {"success": True, "data": new_client_contract}
    except Exception as e:
        db.rollback()
        print("Error adding client contract:", e)
        raise ValueError(f"Failed to add client contract: {e}")
    finally:
        db.close()

async def update_client_contract(payload: EditClientRequest, client_id):
    """
    This function adds or updare a client contract to the ContractClient table based on the EditClientRequest schema.
    Uses LocalSession to add data.
    If no contract_id is provided, it will create a new contract.
    """
    db = SessionLocal()
    try:
        if payload.id_contract:
            # Update existing contract
            client_contract = db.query(ContractClient).filter(ContractClient.id == payload.id_contract).first()
            if not client_contract:
                raise ValueError("Contract not found")
            client_contract.start = datetime.strptime(payload.start_contract, "%d-%m-%Y").date() if payload.start_contract else None
            client_contract.end = datetime.strptime(payload.end_contract, "%d-%m-%Y").date() if payload.end_contract else None
            client_contract.file_contract = payload.file_contract
            db.commit()
            return {"success": True, "data": client_contract}
        else:
            # Create new contract
            new_client_contract = ContractClient(
                client_id=client_id,
                start=datetime.strptime(payload.start_contract, "%d-%m-%Y").date() if payload.start_contract else None,
                end=datetime.strptime(payload.end_contract, "%d-%m-%Y").date() if payload.end_contract else None,
                file_contract=payload.file_contract,
                created_at=datetime.now(tz=timezone(TZ)),
            )
            db.add(new_client_contract)
            db.commit()
            db.refresh(new_client_contract)
            return {"success": True, "data": new_client_contract}
    except Exception as e:
        db.rollback()
        print("Error updating client contract:", e)
        raise ValueError(f"Failed to update client contract: {e}")
    finally:
        db.close()

async def create_custom_id(
        id: int, 
        prefix:Optional[str]="C"
) -> str:
    num_digits = len(str(id))
    formatted_id = f"{id:0{num_digits+1}d}"  
    return prefix + formatted_id

async def add_outlet(outlets:List[ClientOutlet], id_client):
    db = SessionLocal()
    try:
        for data in outlets:
            new_outlet = ClientOutlet(
                client_id = id_client,
                name = data.name,
                longitude = data.longitude,
                latitude = data.latitude,
                address = data.address
            )
            db.add(new_outlet)
            db.commit()
            db.refresh(new_outlet)
            db.execute(
            update(ClientOutlet).where(
                ClientOutlet.id == new_outlet.id)
                .values(id_outlet=await create_custom_id(id=new_outlet.id, prefix='O'))
            )
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in background add outlets task: {e}")
    finally:
        db.close()

async def add_tax_ppn(id_client, user_id):
    db = SessionLocal()
    try:
        # Data preparation
        year_now = int(datetime.now(tz=timezone(TZ)).year)
        tax_name = "PPN"
        tax_percent = 12
        # Check if tax already exist
        exist_tax = db.execute(
            select(Tax)
            .filter(
                Tax.client_id == id_client,
                Tax.isact == True,
                Tax.year == year_now,
                Tax.name == tax_name,
                )
        ).scalar()
        if not exist_tax:
            new_tax = Tax(
                client_id = id_client,
                created_by = user_id,
                name = tax_name,
                percent = tax_percent,
                year = year_now,
            )
            db.add(new_tax)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in background add tax: {e}")
    finally:
        db.close()

async def add_tax_pph(id_client, user_id, basic_salary):
    db = SessionLocal()
    try:
        # Data preparation
        year_now = int(datetime.now(tz=timezone(TZ)).year)
        tax_name = "PPH"

        # Determine tax_percent based on basic_salary
        if (basic_salary*12 <= 60000000):  # Up to 60 million
            tax_percent = 5
        elif (basic_salary*12 <= 250000000):  # 60 million to 250 million
            tax_percent = 15
        elif (basic_salary*12 <= 500000000):  # 250 million to 500 million
            tax_percent = 25
        elif (basic_salary*12 <= 5000000000):  # 500 million to 5 billion
            tax_percent = 30
        else:  # Above 5 billion
            tax_percent = 0

        # Check if tax already exist
        exist_tax = db.execute(
            select(Tax)
            .filter(
                Tax.client_id == id_client,
                Tax.isact == True,
                Tax.year == year_now,
                Tax.name == tax_name,
            )
        ).scalar()
        if not exist_tax:
            new_tax = Tax(
                client_id=id_client,
                created_by=user_id,
                name=tax_name,
                percent=tax_percent,
                year=year_now,
            )
            db.add(new_tax)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error in background add tax: {e}")
    finally:
        db.close()

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

async def edit_validator(db: Session, payload: AddClientRequest, id:str):
    try:
        errors = None
        queries = []
        # For client checking
        # if payload.role_id:
        #     queries.append(select(Client.id).filter(Client.id == payload.role_id).exists())

        if payload.name:
            queries.append(select(Client.id).filter(Client.id_client != id, Client.name == payload.name, Client.isact==True).exists())

        if payload.cs_email:
            queries.append(select(Client.cs_email).filter(Client.id_client != id, Client.cs_email == payload.cs_email, Client.isact==True).exists())

        if payload.cs_number:
            queries.append(select(Client.cs_number).filter(Client.id_client != id, Client.cs_number == payload.cs_email, Client.isact==True).exists())

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

async def edit_client(
    db: Session,
    user: User,
    payload: EditClientRequest,
    background_tasks: any,
    client_id: str,
) -> Client:
    """
    This function only updates fields that are not null.
    """
    try:
        # If changes photo
        if payload.photo:
            photo_path = os.path.join("client", payload.photo.split("/")[-1])
            photo_url = upload_file_from_path_to_minio(minio_path=photo_path, local_path=payload.photo)
            print(photo_path)
        else:
            photo_path = None

        client = db.execute(select(Client).filter(Client.id_client == client_id)).scalar()
        if not client:
            raise ValueError("Client not found")
        if payload.payment_date:
            due_date_payment = datetime.strptime(payload.payment_date, "%d-%m-%Y").date()
        else:
            due_date_payment = None


        # Update fields only if they are not null
        client.photo = photo_path if payload.photo else client.photo
        client.name = payload.name if payload.name else client.name
        client.address = payload.address if payload.address else client.address
        client.fee_agency = payload.agency_fee if payload.agency_fee is not None else client.fee_agency
        client.due_date_payment = due_date_payment if payload.payment_date else client.due_date_payment
        client.cs_person = payload.cs_person if payload.cs_person else client.cs_person
        client.cs_number = payload.cs_number if payload.cs_number else client.cs_number
        client.cs_email = payload.cs_email if payload.cs_email else client.cs_email
        client.updated_by = user.id

        db.add(client)
        db.commit()

        # Handle related entities
        if isinstance(payload.outlet, (list, tuple)):
            background_tasks.add_task(
                edit_outlet,
                payload.outlet,
                client.id,
            )
        if isinstance(payload.bpjs, (list, tuple)):
            background_tasks.add_task(
                edit_bpjs,
                payload.bpjs,
                client.id,
            )
        if isinstance(payload.allowences, (list, tuple)):
            background_tasks.add_task(
                edit_allowences,
                payload.allowences,
                client.id,
            )

        # Contract Handler
        if payload.start_contract or payload.end_contract or payload.file_contract:
            background_tasks.add_task(
                update_client_contract,
                payload=payload,
                client_id=client.id,
            )

        # Tax handler
        data_tax = {
            "id_client": client.id,
            "user_id": user.id,
        }
        background_tasks.add_task(
            add_tax_ppn,
            **data_tax
        )
        data_tax_pph = {
            "id_client": client.id,
            "user_id": user.id,
            "basic_salary": client.basic_salary,  # Fetch basic_salary from the client object
        }
        background_tasks.add_task(
            add_tax_pph,
            **data_tax_pph
        )

        # Client payment handler
        background_tasks.add_task(
            add_client_payment,
            client.id,
        )
        return "oke"
    except Exception as e:
        db.rollback()
        db.execute(
            update(Client)
            .where(Client.id == client.id)
            .values(isact=False)
        )
        db.commit()
        raise ValueError(e)
    
async def edit_bpjs(data, client_id):
    db = SessionLocal()  # Ambil koneksi dari pool
    db.execute(
    update(Bpjs).where(
        Bpjs.client_id==client_id)
        .values(isact=False)
    )
    db.commit()
    try:
        for d in data:
            if d.id == None:
                new_bpjs = Bpjs(
                    client_id = client_id,
                    name = d.name,
                    amount = d.amount
                )
                db.add(new_bpjs)
                db.commit()
            else: 
                exist_data = db.execute(
                    select(Bpjs)
                    .filter(Bpjs.id==d.id)
                ).scalar()
                exist_data.isact=True
                exist_data.name=d.name
                exist_data.amount=d.amount
                db.add(exist_data)
                db.commit()
        return "oke"                
    except Exception as e:
        print("Error edit bpjs: \n", e)
    finally:
        db.close()  # Always ensure connection is closed properly
async def edit_allowences(data, client_id):
    db = SessionLocal()  # Ambil koneksi dari pool
    db.execute(
    update(Allowances).where(
        Allowances.client_id==client_id)
        .values(isact=False)
    )
    db.commit()
    try:
        for d in data:
            if d.id == None:
                new_allowances = Allowances(
                    client_id = client_id,
                    name = d.name,
                    amount = d.amount
                )
                db.add(new_allowances)
                db.commit()
            else: 
                exist_data = db.execute(
                    select(Allowances)
                    .filter(Allowances.id==d.id)
                ).scalar()
                exist_data.isact=True
                exist_data.name=d.name
                exist_data.amount=d.amount
                db.add(exist_data)
                db.commit()
        return "oke"                
    except Exception as e:
        print("Error edit allowence: \n", e)
    finally:
        db.close()  # Always ensure connection is closed properly
async def edit_outlet(data, client_id):
    db = SessionLocal()  # Ambil koneksi dari pool
    db.execute(
    update(ClientOutlet).where(
        ClientOutlet.client_id==client_id)
        .values(isact=False)
    )
    db.commit()
    try:
        for d in data:
            if d.id_outlet == None:
                new_outlet = ClientOutlet(
                    client_id = client_id,
                    name = d.name,
                    longitude = d.longitude,
                    latitude = d.latitude,
                    address = d.address
                )
                db.add(new_outlet)
                db.commit()
                db.refresh(new_outlet)
                db.execute(
                update(ClientOutlet).where(
                    ClientOutlet.id == new_outlet.id)
                    .values(id_outlet=await create_custom_id(id=new_outlet.id, prefix='O'))
                )
                db.commit()
            else: 
                exist_data = db.execute(
                    select(ClientOutlet)
                    .filter(ClientOutlet.id_outlet==d.id_outlet)
                ).scalar()
                exist_data.isact=True
                exist_data.name=d.name
                exist_data.longitude=d.longitude
                exist_data.latitude=d.latitude
                exist_data.address=d.address
                db.add(exist_data)
                db.commit()
        return "oke"                
    except Exception as e:
        print("Error edit outlet: \n", e)
    finally:
        db.close()  # Always ensure connection is closed properly
    
async def list_client(
    db:Session,
    src:Optional[str]=None,
    page:Optional[int]=1,
    page_size:Optional[int]=10,
    user:Optional[User]=None,
):
    try:        
        limit = page_size
        offset = (page - 1) * limit

        query = (
            select(Client)
            .filter(Client.isact==True)
        )
        query_count = (
            select(func.count(Client.id))
            .filter(Client.isact==True)
        )

        # Admin hanya client dia aj
        if user:
            if user.roles[0].id==2:
                query = query.filter(Client.id == user.client_id)
                query_count = query_count.filter(Client.id == user.client_id)

        if src:
            query = (query
                     .filter(or_(
                         Client.name.ilike(f"%{src}%"),
                         Client.address.ilike(f"%{src}%")
                        ))
                     )
            query_count = (query_count
                     .filter(or_(
                         Client.name.ilike(f"%{src}%"),
                         Client.address.ilike(f"%{src}%")
                        ))
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
                } for d in (item.outlets or []) if d.isact
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
    db: Session,
    id: int
) -> DetailClient:
    try:
        query = select(Client).filter(Client.id_client == id).limit(1)
        client = db.execute(query).scalar()
        return await formatin_detail(client)
    except Exception as e:
        print("Error detail: \n", e)
        raise ValueError("Failed to get detail client")

async def formatin_detail(data: Client) -> DetailClient:
    """
    Format the client data to match the DetailClient Pydantic model.
    """
    if not data:
        raise ValueError("Client not found")

    # Extract contract data (if available)
    contract = data.contract_clients[0] if data.contract_clients else None

    return DetailClient(
        id=str(data.id_client),  # Ensure id is a string
        photo=generate_link_download(data.photo) if data.photo else None,  # Optional[str]
        name=data.name,  # str
        address=data.address,  # Optional[str]
        outlet=[
            OutletList(
                id_outlet=str(outlet.id_outlet) if outlet.id_outlet else None,  # Optional[str]
                name=outlet.name,  # str
                total_active=len([o for o in data.outlets if o.isact]),  # int
                address=outlet.address,  # str
                latitude=float(outlet.latitude),  # float
                longitude=float(outlet.longitude)  # float
            )
            for outlet in (data.outlets or []) if outlet.isact
        ] if data.outlets else [],  # Optional[List[OutletList]]
        basic_salary=float(data.basic_salary) if data.basic_salary is not None else None,  # Optional[float]
        agency_fee=float(data.fee_agency) if data.fee_agency is not None else None,  # Optional[float]
        payment_date=data.due_date_payment.strftime("%d-%m-%Y") if data.due_date_payment else None,  # Optional[str]
        bpjs=[
            EditBpjsRequest(
                id=int(bpjs.id),  # Optional[int]
                name=bpjs.name,  # str
                amount=float(bpjs.amount)  # float
            )
            for bpjs in (data.bpjs or []) if bpjs.isact
        ] if data.bpjs else [],  # Optional[List[EditBpjsRequest]]
        allowences=[
            EditAllowencesRequest(
                id=int(allowance.id),  # Optional[int]
                name=allowance.name,  # str
                amount=float(allowance.amount)  # float
            )
            for allowance in (data.allowances or []) if allowance.isact
        ] if data.allowances else [],  # Optional[List[EditAllowencesRequest]]
        cs_person=data.cs_person,  # Optional[str]
        cs_number=data.cs_number,  # Optional[str]
        cs_email=data.cs_email,  # Optional[str]
        id_contract=str(contract.id) if contract else None,  # Optional[str]
        start_contract=contract.start.strftime("%d-%m-%Y") if contract and contract.start else None,  # Optional[str]
        end_contract=contract.end.strftime("%d-%m-%Y") if contract and contract.end else None,  # Optional[str]
        file_contract=contract.file_contract if contract else None  # Optional[str]
    ).model_dump()


async def edit_outlet_bak(
    db:Session,
    user:User,
    id_outlet:str,
    payload:EditOutletRequest,
):
    try:
        exist_data=db.execute(
            select(ClientOutlet)
            .filter(ClientOutlet.id_outlet==id_outlet)
            .limit(1)
        ).scalar()
        if not exist_data:
            raise ValueError("Data not found")
        exist_data.updated_at=datetime.now(tz=timezone(TZ))
        exist_data.updated_by=user.id
        exist_data.name=payload.name
        exist_data.address=payload.address
        exist_data.latitude=payload.latitude
        exist_data.longitude=payload.longitude
        # exist_data.total_active=payload.total_active
        db.add(exist_data)
        db.commit()
        return "Oke"
    except Exception as e:
        print("Error edit outlet", e)
        raise ValueError("Failed edit data")
    
async def delete_outlet(
    db:Session,
    user:User,
    id_outlet:str,
):
    try:
        exist_data=db.execute(
            select(ClientOutlet)
            .filter(ClientOutlet.id_outlet==id_outlet)
            .limit(1)
        ).scalar()
        if not exist_data:
            raise ValueError("Data not found")
        exist_data.updated_at=datetime.now(tz=timezone(TZ))
        exist_data.updated_by=user.id
        exist_data.isact=not exist_data.isact
        # exist_data.total_active=payload.total_active
        db.add(exist_data)
        db.commit()
        return "Oke"
    except Exception as e:
        print("Error edit outlet", e)
        raise ValueError("Failed edit data")
    
async def get_detail_client(
    db: Session,
    id_client: str,
) -> DataDetailClientSignature:
    try:
        # Query the client with related data using subqueryload for optimization
        result = (
            db.query(Client)
            .options(
                subqueryload(Client.outlets),
                subqueryload(Client.allowances),
                subqueryload(Client.bpjs),
                subqueryload(Client.contract_clients),
                subqueryload(Client.client_tax),
            )
            .filter(Client.id_client == id_client, Client.isact == True)
            .first()
        )

        if not result:
            raise ValueError("Client not found")

        # Convert the result to a Pydantic model
        client_data = to_pydantic(result)
        return client_data

    except Exception as e:
        print("Error get detail client:\n", e)
        raise ValueError("Failed to get detail client")


def to_pydantic(result: Client) -> DataDetailClientSignature:
    if not result:
        return None

    # Parse outlets
    outlets = [
        OutletList(
            id_outlet=outlet.id_outlet,
            name=outlet.name,
            total_active=len([o for o in result.outlets if o.isact]),  # Calculate total active outlets
            address=outlet.address,
            latitude=outlet.latitude,
            longitude=outlet.longitude,
        )
        for outlet in result.outlets if outlet.isact
    ]

    # Parse payroll
    payroll = PayrollClient(
        basic_salary=float(result.basic_salary) if result.basic_salary is not None else None,
        agency_fee=float(result.fee_agency) if result.fee_agency is not None else None,
        allowance=sum(float(allowance.amount) for allowance in result.allowances if allowance.isact),
        total_deduction=0.0,  # Placeholder for total_deduction
        nett_payment=0.0,  # Placeholder for nett_payment
        due_date=result.due_date_payment.strftime("%d-%m-%Y") if result.due_date_payment else None,
    )

    # Combine into DataDetailClientSignature
    return DataDetailClientSignature(
        name=result.name,
        address=result.address,
        id_client=result.id_client,
        outlet=outlets,
        payroll=payroll,
        total_active=len(outlets),  # Total active outlets
        manager_signature=result.contract_clients[0].manager_signature if result.contract_clients else None,
        technical_signature=result.contract_clients[0].technical_signature if result.contract_clients else None,
        cs_person=result.cs_person,
        cs_number=result.cs_number,
        cs_email=result.cs_email,
        contract_date=(
            f"{result.contract_clients[0].start.strftime('%d-%m-%Y')} - {result.contract_clients[0].end.strftime('%d-%m-%Y')}"
            if result.contract_clients and result.contract_clients[0].start and result.contract_clients[0].end
            else None
        ),
        contract_file=generate_link_download(result.contract_clients[0].file_contract) if result.contract_clients else None,
    ).model_dump()

# Panggil fungsi
# client_data = to_pydantic(result)
# if client_data:
#     print(client_data.dict())