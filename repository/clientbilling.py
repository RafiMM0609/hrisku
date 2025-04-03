from typing import Optional, List
from math import ceil
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from models.Client import Client
from core.file import generate_link_download
from models.User import User
from models.ClientPayment import ClientPayment
from models.ContractClient import ContractClient
from models.Tax import Tax
from models.Allowances import Allowances
from models.Bpjs import Bpjs
from models import SessionLocal
from pytz import timezone
from settings import TZ
from math import ceil
from schemas.clientbilling import (
    ListDetailBilling,
    Organization,
    ListDetailKeterangan,
    ListDetailBillingAction,
    )
from pydantic import BaseModel
from datetime import datetime, timedelta, time, date

async def list_billing_action(
    db: Session,
    id: str,
) -> ListDetailBillingAction:
    try:
        # Query ClientPayment dengan eager loading untuk menghindari query tambahan
        # query = (
        #     select(ClientPayment)
        #     .join(Client, Client.id == ClientPayment.client_id, isouter=True)
        #     .options(
        #         joinedload(ClientPayment.clients).joinedload(Client.client_tax),
        #         joinedload(ClientPayment.clients).joinedload(Client.allowances),
        #         joinedload(ClientPayment.clients).joinedload(Client.bpjs),
        #         joinedload(ClientPayment.clients).joinedload(Client.user_client),
        #     )
        #     .filter(ClientPayment.isact == True, ClientPayment.id == id)
        #     .limit(1)
        # )
        # payment = db.execute(query).scalar_one_or_none()
        payment = (
            db.query(ClientPayment)
            .join(Client, Client.id == ClientPayment.client_id)
            .options(
                joinedload(ClientPayment.clients).joinedload(Client.client_tax),
                joinedload(ClientPayment.clients).joinedload(Client.allowances),
                joinedload(ClientPayment.clients).joinedload(Client.bpjs),
                joinedload(ClientPayment.clients).joinedload(Client.user_client),
            )
            .filter(ClientPayment.isact == True, ClientPayment.id == id)
            .first()
        )

        if not payment:
            return ListDetailBillingAction(
                title=None,
                client_id=None,
                client_name=None,
                start_period=None,
                end_period=None,
                detail=[]
            ).dict()

        client = payment.clients
        taxes = client.client_tax
        allowances = client.allowances
        bpjs_data = client.bpjs
        month_year = payment.date.strftime("%d-%m-%Y") if payment.date else "N/A"

        detail_items = []
        total_nominal = 0.000

        # Initiate fungsi for append data to ListDetail
        def add_detail_item(keterangan, nominal=None, jumlah=None):
            detail_items.append(
                ListDetailKeterangan(
                    keterangan=keterangan,
                    nominal=nominal,
                    jumlah=jumlah
                )
            )

        # Total Salary Initiate
        basic_salary = client.basic_salary or 0.00
        total_employee = len(client.user_client)
        total_nominal = 0.00
        total_bpjs = 0.00
        total_taxes = 0.00

        # Perhitungan untuk setiap karyawan
        for _ in range(total_employee):
            # Perhitungan BPJS per karyawan
            for bpjs in bpjs_data:
                bpjs_amount = ((bpjs.amount or 0) / 100) * basic_salary
                total_bpjs += bpjs_amount
                total_nominal += bpjs_amount

            # Perhitungan Tax per karyawan
            for tax in taxes:
                tax_amount = ((tax.percent or 0) / 100) * (basic_salary * 12)
                total_taxes += tax_amount
                total_nominal += tax_amount

        # Total Gaji Awal
        total_gaji_awal = basic_salary * total_employee
        total_nominal += total_gaji_awal

        # Add Allowances
        for allowance in allowances:
            allowance_amount = allowance.amount or 0
            total_nominal += allowance_amount
            add_detail_item(f"Allowance {allowance.name}", nominal=allowance_amount)

        # Add BPJS to detail
        add_detail_item("Total BPJS", nominal=total_bpjs)

        # Add Taxes to detail
        add_detail_item("Total Taxes", nominal=total_taxes)

        # Add Total Biaya Operasional
        add_detail_item("Total Biaya Operasional", jumlah=total_nominal)

        # Agency Fee
        agency_fee = (client.fee_agency or 0) / 100 * total_nominal
        total_nominal += agency_fee
        add_detail_item(f"Agency Fee {client.fee_agency}%", nominal=agency_fee)

        # Grand Total
        add_detail_item("Grand Total", jumlah=total_nominal)


        # Response
        result = ListDetailBillingAction(
            title="Laporan Pengeluaran Biaya",
            client_id=client.id,
            client_name=client.name,
            start_period=month_year,
            end_period=month_year,
            detail=detail_items
        ).dict()

        return result
    except Exception as e:
        print(f"Failed to get billing action: {str(e)}")
        raise ValueError("Failed to get billing action")

async def list_client_billing(
    db:Session,
    src:Optional[str]=None,
    page:Optional[int]=1,
    page_size:Optional[int]=10,
    user:Optional[User]=None,
):
    try:        
        limit = page_size
        offset = (page - 1) * limit

        query = (select(Client).filter(Client.isact==True)
        )
        query_count = (select(func.count(Client.id)).filter(Client.isact==True)
        )

        if user:
            print("Ini role user : \n", user.roles[0].id)
            if user.roles[0].id==2:
                query = (query.filter(Client.id_client==user.client_id))
                query_count = (query_count.filter(Client.id_client==user.client_id))

        if src:
            query = (query
                     .filter(or_(
                         (Client.name.ilike(f"%{src}%")),
                         (Client.address.ilike(f"%{src}%")),
                     ))
                     )
            query_count = (query_count
                        .filter(or_(
                            (Client.name.ilike(f"%{src}%")),
                            (Client.address.ilike(f"%{src}%")),
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
    
async def formating_client(data:List[Client]):
    if not data:
        return []

    result = []
    for item in data:
        result.append({
            "id": item.id_client,
            "name": item.name,
            "address": item.address,
            "created_at": item.created_at.astimezone(
            timezone(TZ)
            ).strftime("%d-%m-%Y %H:%M:%S") if item.created_at else None,
            "isact": item.isact,
            "payment_status": item.payment_status,
        })
    return result

async def list_detail_cb(
    id: int,
    db: Session,
    user: User,
    src: Optional[str] = None,
    page: Optional[int] = 1,
    page_size: Optional[int] = 10,
) -> tuple[List[ListDetailBilling], int, int]:
    try:
        limit = page_size
        offset = (page - 1) * limit
        
        query = (select(ClientPayment)
                 .outerjoin(Client, Client.id == ClientPayment.client_id)
                 .filter(ClientPayment.isact == True)
                 .filter(Client.id_client == id))
                 
        query_count = (select(func.count(ClientPayment.id))
                 .outerjoin(Client, Client.id == ClientPayment.client_id)
                 .filter(ClientPayment.isact == True)
                 .filter(Client.id_client == id))
        
        query = (query.order_by(ClientPayment.id.asc())
                .limit(limit=limit)
                .offset(offset=offset))
        
        data = db.execute(query).scalars().all()
        num_data = db.execute(query_count).scalar()
        num_page = ceil(num_data / limit)
        
        result = []
        for item in data:
            result.append(ListDetailBilling(
                id=str(item.id),
                date=item.date.strftime("%B %Y") if item.date else None,
                client_id=item.client_id,
                amount=item.amount,
                total_talent= len(item.clients.user_client) if hasattr(item, 'clients') else 0,
                status=Organization(
                    id=item.status_id if hasattr(item, 'status_id') else 0, 
                    name=item.status_payment.name if item.status_payment else None),
                evidence_payment=generate_link_download(item.evidence_payment) if hasattr(item, 'evidence_payment') else "",
                verify=item.status_id == 1 if hasattr(item, 'status_id') else False
            ).model_dump())
        
        return (result, num_data, num_page)
    except Exception as e:
        print("Error list detail: \n", e)
        raise ValueError("Failed get data list payment client")
    

async def add_client_payment(client_id):
    db = SessionLocal()
    try:
        # Fetch the end date of the contract from ContractClient
        contract = (
            db.query(ContractClient)
            .filter(ContractClient.client_id == client_id)
            .order_by(ContractClient.end.desc())
            .first()
        )
        if not contract or not contract.end:
            raise ValueError("Contract end date not found for the given client.")

        date = contract.end_date  # Use the end date of the contract
        # Query ClientPayment dengan eager loading untuk menghindari query tambahan
        query = (
            select(Client)
            .options(
                joinedload(Client.client_tax),
                joinedload(Client.allowances),
                joinedload(Client.bpjs),
                joinedload(Client.user_client),
            )
            .filter(Client.isact == True, Client.id == client_id)
            .limit(1)
        )
        client = db.execute(query).scalar_one_or_none()
        taxes = client.client_tax
        allowances = client.allowances
        bpjs_data = client.bpjs
        user_client = client.user_client

        # Initialize total nominal with basic salary
        total_nominal = 0.00
        basic_salary = client.basic_salary or 0.00
        basic_salary_in_period = basic_salary * 12
        total_employee = len(user_client)
        total_gaji_awal = basic_salary_in_period * total_employee
        total_nominal += total_gaji_awal

        # Perhitungan pergaji karyawan
        for _ in range(total_employee):  # Corrected loop syntax
            # Add BPJS
            total_bpjs = 0.00
            for item in bpjs_data:
                bpjs_amount = ((item.amount or 0) / 100) * basic_salary
                total_bpjs += bpjs_amount
                total_nominal += bpjs_amount

            # Add Taxes (percentage-based)
            total_taxes = 0.00
            for tax in taxes:
                tax_amount = ((tax.percent or 0) / 100) * basic_salary_in_period
                total_taxes += tax_amount
                total_nominal += tax_amount

        # Add Allowances
        total_allowances = sum(allowance.amount or 0 for allowance in allowances)
        total_nominal += total_allowances

        # # Add BPJS
        # total_bpjs = 0.00
        # for item in bpjs_data:
        #     bpjs_amount = (item.percent or 0) * total_gaji_awal
        #     total_bpjs += bpjs_amount
        #     total_nominal += bpjs_amount

        # # Add Taxes (percentage-based)
        # total_taxes = 0
        # for tax in taxes:
        #     tax_amount = (tax.percent or 0) * total_gaji_awal
        #     total_taxes += tax_amount
        #     total_nominal += tax_amount

        # Grand Total
        grand_total = total_nominal

        # Check if data already exists
        existing_payment = (
            db.query(ClientPayment)
            .filter(ClientPayment.client_id == client_id, ClientPayment.date == date)
            .first()
        )

        if existing_payment:
            # Update existing record
            existing_payment.amount = grand_total
        else:
            # Add new record
            new_payment = ClientPayment(
                client_id=client_id,
                date=date,
                amount=grand_total,
                status_id=1,
            )
            db.add(new_payment)

        db.commit()
        return "oke"
    except Exception as e:
        print("Error add client payment: \n", e)
        raise ValueError("Failed to add client payment")
    finally:
        db.close()

