from typing import Optional
from math import ceil
import secrets
from sqlalchemy import select, func, distinct
from sqlalchemy.orm import Session, aliased
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.performance import (
    PerformanceRequest,
    EditPerformanceRequest
    )
import os
import asyncio
from models.Performance import Performance
from models.User import User

async def add_performance(
    db: Session,  
    emp_id: str,  # User ID
    data: PerformanceRequest,
):
    try:
        # Get first day of the month
        today = datetime.now().date()
        first_day_of_month = today.replace(day=1)

        # Get data user evaluated
        data_user = db.execute(
            select(User.client_id, User.isact)
            .filter(User.id == emp_id)
        ).fetchone()
        
        if not data_user:
            raise ValueError(f"User with ID {emp_id} not found")

        # Generate model from the request data
        performance_data = Performance(
            emp_id=emp_id,
            client_id=data_user[0],
            date=today,
            softskill=data.softskill,
            hardskill=data.hardskill,
            notes=data.note,
            created_at=datetime.now(timezone(TZ)),
            created_by=emp_id,
        )

        db.add(performance_data)
        db.commit()
        db.refresh(performance_data)
        return performance_data.id
    except ValueError as ve:
        db.rollback()
        print(f"Validation error in add_performance: {str(ve)}")
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in add_performance: {str(e)}")
        raise ValueError(f"Error in add_performance: {str(e)}")

async def edit_performance(
    db: Session,
    performance_id: int,
    data: EditPerformanceRequest,
    user: User
):
    try:
        # Find the existing performance record
        performance_data = db.query(Performance).filter(Performance.id == performance_id).first()
        
        if not performance_data:
            raise ValueError(f"Performance record with ID {performance_id} not found")
            
        # Update the fields with new values
        if data.softskill is not None:
            performance_data.softskill = data.softskill
        if data.hardskill is not None:
            performance_data.hardskill = data.hardskill
        if data.note is not None:
            performance_data.notes = data.note
            
        # Update metadata
        performance_data.updated_at = datetime.now(timezone(TZ))
        performance_data.updated_by = user.id
        
        # Commit changes
        db.commit()
        db.refresh(performance_data)
        return performance_data.id
    except ValueError as ve:
        db.rollback()
        print(f"Validation error in edit_performance: {str(ve)}")
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in edit_performance: {str(e)}")
        raise ValueError(f"Error in edit_performance: {str(e)}")
