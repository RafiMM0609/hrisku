from typing import Optional, List
from math import ceil
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models.Client import Client
from core.file import generate_link_download
from models.User import User
from models.ClientPayment import ClientPayment
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
from datetime import date

async def list_billing_action(
    db: Session,
    id: str,
) -> ListDetailBillingAction:
    try:
        # Query the ClientPayment with its related Client
        query = (
            select(ClientPayment)
            .join(Client, Client.id == ClientPayment.client_id)
            .filter(ClientPayment.isact == True, ClientPayment.id == id)
            .limit(1)
        )
        payment = db.execute(query).scalar_one_or_none()
        
        if not payment:
            raise ValueError(f"ClientPayment not found")
        
        client = payment.clients
        
        # Get related data
        taxes = client.client_tax
        allowances = client.allowances
        bpjs_data = client.bpjs
        
        # Format period dates
        month_year = payment.date.strftime("%d-%m-%Y") if payment.date else "N/A"
        
        # Build detail items
        detail_items = []
        total_nominal = 0
    
        # Total Salary
        basic_salary = client.basic_salary
        total_employee = len(client.user_client)
        total_nominal += basic_salary * total_employee

        # Biaya Operasional
        detail_items.append(
        ListDetailKeterangan(
            keterangan=f"Biaya Operasional",
            nominal=total_nominal,
            jumlah=None  # Not updating jumlah for individual items
        )
        )

        # Add allowance details
        for allowance in allowances:
            allowance_amount = float(allowance.amount) if allowance.amount else 0
            total_nominal += allowance_amount
            detail_items.append(
            ListDetailKeterangan(
                keterangan=f"Allowance: {allowance.name}",
                nominal=allowance_amount,
                jumlah=None  # Not updating jumlah for individual items
            )
            )
        
        # Add BPJS details
        for bpjs in bpjs_data:
            bpjs_amount = float(bpjs.amount) if bpjs.amount else 0
            total_nominal += bpjs_amount
            detail_items.append(
            ListDetailKeterangan(
                keterangan=f"BPJS: {bpjs.name}",
                nominal=bpjs_amount,
                jumlah=None  # Not updating jumlah for individual items
            )
            )

        # Total Biaya Operasional
        detail_items.append(
        ListDetailKeterangan(
            keterangan=f"Total Biaya Operasional",
            nominal=None,
            jumlah=total_nominal  # updating jumlah for total
        )
        )

        # Add agency fee
        agency_fee=client.fee_agency*total_nominal
        total_nominal += agency_fee
        detail_items.append(
            ListDetailKeterangan(
                keterangan=f"Agency Fee {client.fee_agency}",
                nominal=agency_fee,
                jumlah=None  # Not updating jumlah for individual items
            )
        )

        # Jumlah Biaya
        detail_items.append(
            ListDetailKeterangan(
                keterangan=f"Jumlah Biaya",
                nominal=None,
                jumlah=total_nominal  # updating jumlah for amount
            )
        )
        # Add tax details
        for tax in taxes:
            tax_nominal = float(tax.percent) if tax.percent else 0
            amount_tax = tax_nominal * total_nominal
            total_nominal += amount_tax
            detail_items.append(
            ListDetailKeterangan(
                keterangan=f"Tax: {tax.name}-{tax.percent}",
                nominal=tax_nominal,
                jumlah=None  # Not updating jumlah for individual items
            )
            )
        
        # Add Final Grand Total
        detail_items.append(
            ListDetailKeterangan(
                keterangan="Grand Total",
                nominal=None,
                jumlah=total_nominal # updating jumlah for amount
            )
        )
        
        # Create response object
        result = ListDetailBillingAction(
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
                status=Organization(id=item.status_id if hasattr(item, 'status_id') else 0, 
                                   name="dummy"),
                evidence_payment=generate_link_download(item.evidence_payment) if hasattr(item, 'evidence_payment') else ""
            ).model_dump())
        
        return (result, num_data, num_page)
    except Exception as e:
        print("Error list detail: \n", e)
        raise ValueError("Failed get data list payment client")

    