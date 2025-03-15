from typing import Optional, List
from math import ceil
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models.Client import Client
from models.User import User
from models.ClientPayment import ClientPayment
from pytz import timezone
from settings import TZ
from math import ceil

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
    id:id,
    db:Session,
    user:User,
    src:Optional[str]=None,
    page:Optional[int]=1,
    page_size:Optional[int]=10,
):
    try:
        limit = page_size
        offset = (page - 1) * limit
        query = (select(ClientPayment)
                 .filter(ClientPayment.isact==True)
                 .filter(ClientPayment.client_id==id)
        )
        query_count = (select(func.count(ClientPayment.id))
                .filter(ClientPayment.isact==True)
                .filter(ClientPayment.client_id==id)
        )
        query = (
            query.order_by(ClientPayment.id.asc())
            .limit(limit=limit)
            .offset(offset=offset)
        )
        data = db.execute(query).scalars().all()
        num_data = db.execute(query_count).scalar()
        num_page = ceil(num_data / limit)
        return (await formating_billing(data), num_data, num_page)
    except Exception as e:
        print("Error list detail: \n", e)
        raise ValueError("Failed get data list payment client")
async def formating_billing(data):
    if not data:
        return []

    result = []
    for item in data:
        result.append({
            "id": item.id,
            "client_id": item.client_id,
            "amount": item.amount,
            "date": item.date.strftime("%d-%m-%Y") if item.date else None,
            "isact": item.isact,
        })
    return result

    