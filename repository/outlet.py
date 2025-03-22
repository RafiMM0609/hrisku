from typing import Optional, List
from math import ceil
from sqlalchemy import select, func, distinct, update
from sqlalchemy.orm import Session, joinedload, subqueryload
from core.file import upload_file_to_local, delete_file_in_local, generate_link_download
from models.ClientOutlet import ClientOutlet
from datetime import datetime, timedelta
from pytz import timezone
import os
import asyncio
from math import ceil
from schemas.outlet import (
    OutletOption
)

async def get_outlets(
    db: Session,
    client_id:Optional[str]=None,
    src: Optional[str] = None
) -> List[OutletOption]:
    try:
        query = (
            select(ClientOutlet)
            .where(ClientOutlet.isact == True)
            .order_by(ClientOutlet.id.asc())
        )

        if src:
            query = query.filter(ClientOutlet.name.ilike(f"%{src}%"))
            
        if client_id:
            query = query.filter(ClientOutlet.client_id == client_id)
        
        result = db.execute(query).scalars().all()
        
        outlets = []
        for outlet in result:
            outlets.append(
                OutletOption(
                    id=outlet.id,
                    outlet_id=outlet.id_outlet,
                    name=outlet.name,
                    address=outlet.address,
                    latitude=float(outlet.latitude) if outlet.latitude else None,
                    longitude=float(outlet.longitude) if outlet.longitude else None
                ).dict()
            )
        
        return outlets
    except Exception as e:
        print("Error get_outlets", e)
        raise ValueError("Error get_outlets")   