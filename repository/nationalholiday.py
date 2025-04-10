"""
This file need sets to user KIS (keep it simple) method
this file build to create and update data to National Holiday table
"""
import calendar
from typing import List
from core.rafiexcel import RafiExcel, blue_fill, yellow_fill
from models import SessionLocal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, date
from models.Client import Client
from models.NationalHoliday import NationalHoliday
from models.AttendanceSummary import AttendanceSummary
from models.Attendance import Attendance
from models.Contract import Contract
from models.ShiftSchedule import ShiftSchedule
from models.User import User
from tempfile import NamedTemporaryFile
from starlette.datastructures import UploadFile
from core.file import upload_file, upload_file_to_tmp
import io
import aiohttp
from schemas.nationalholiday import (
    DataNationalHoliday, 
    DataHolidayRequest,
    DataHolidayAddRequest,
)
from pydantic import ValidationError


async def create_update_national_holiday(client_id: int):
    """
    Optimized function to create or update national holiday data.
    """
    db: Session = SessionLocal()
    try:
        open_api_url = "https://api-harilibur.vercel.app/api"

        # Fetch data from the Open API
        async with aiohttp.ClientSession() as session:
            async with session.get(open_api_url) as response:
                if response.status == 200:
                    holidays = await response.json()
                else:
                    raise ValueError(f"Failed to fetch data from API. Status code: {response.status}")

        # Fetch existing holidays in a single query
        existing_holidays = db.query(NationalHoliday).filter(
            NationalHoliday.client_id == client_id,
            NationalHoliday.isact==True,
        ).all()
        existing_holidays_map = {
            (holiday.date, holiday.name): holiday for holiday in existing_holidays
        }

        # Prepare new and updated records
        new_holidays = []
        for holiday in holidays:
            holiday_date = holiday.get("holiday_date")
            holiday_name = holiday.get("holiday_name")
            is_national_holiday = holiday.get("is_national_holiday", True)

            if not holiday_date or not holiday_name:
                continue  # Skip invalid data
            # Convert string date to date object
            holiday_date = datetime.strptime(holiday_date, "%Y-%m-%d").date()
            key = (holiday_date, holiday_name)
            if key in existing_holidays_map:
                # Update the existing record
                existing_holiday = existing_holidays_map[key]
                existing_holiday.is_national = is_national_holiday
                existing_holiday.updated_at = datetime.now()
                db.add(existing_holiday)
            else:
                # Create a new record
                new_holidays.append(NationalHoliday(
                    name=holiday_name,
                    date=holiday_date,
                    note="National Holiday" if is_national_holiday else "Local Holiday",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_national=is_national_holiday,
                    client_id=client_id,
                ))

        # Bulk insert new holidays
        if new_holidays:
            db.bulk_save_objects(new_holidays)

        await create_update_national_holiday_default(0, db)

        # Commit the transaction
        db.commit()
    except Exception as e:
        print(f"Error in create_update_national_holiday: {e}")
        raise ValueError(f"Error in create_update_national_holiday: {e}")
    finally:
        db.close()

async def create_update_national_holiday_default(
    client_id: int,
    db: Session,
):
    """
    Optimized function to create or update national holiday data.
    """
    try:
        open_api_url = "https://api-harilibur.vercel.app/api"

        # Fetch data from the Open API
        async with aiohttp.ClientSession() as session:
            async with session.get(open_api_url) as response:
                if response.status == 200:
                    holidays = await response.json()
                else:
                    raise ValueError(f"Failed to fetch data from API. Status code: {response.status}")

        # Fetch existing holidays in a single query
        existing_holidays = db.query(NationalHoliday).filter(
            NationalHoliday.client_id == client_id,
            NationalHoliday.isact==True,
        ).all()
        existing_holidays_map = {
            (holiday.date, holiday.name): holiday for holiday in existing_holidays
        }

        # Prepare new and updated records
        new_holidays = []
        for holiday in holidays:
            holiday_date = holiday.get("holiday_date")
            holiday_name = holiday.get("holiday_name")
            is_national_holiday = holiday.get("is_national_holiday", True)

            if not holiday_date or not holiday_name:
                continue  # Skip invalid data
            # Convert string date to date object
            holiday_date = datetime.strptime(holiday_date, "%Y-%m-%d").date()
            key = (holiday_date, holiday_name)
            if key in existing_holidays_map:
                # Update the existing record
                existing_holiday = existing_holidays_map[key]
                existing_holiday.is_national = is_national_holiday
                existing_holiday.updated_at = datetime.now()
                db.add(existing_holiday)
            else:
                # Create a new record
                new_holidays.append(NationalHoliday(
                    name=holiday_name,
                    date=holiday_date,
                    note="National Holiday" if is_national_holiday else "Local Holiday",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    is_national=is_national_holiday,
                    client_id=client_id,
                ))

        # Bulk insert new holidays
        if new_holidays:
            db.bulk_save_objects(new_holidays)

        # Commit the transaction
        db.commit()
    except Exception as e:
        print(f"Error in create_update_national_holiday: {e}")
        raise ValueError(f"Error in create_update_national_holiday: {e}")

async def create_data_national_holiday(
    db: Session,
    payload: DataHolidayAddRequest,
    user: User,
):
    
    """
    This function is used to create a new national holiday record.
    """
    try:
        new_holiday = NationalHoliday(
            name=payload.name,
            date=datetime.strptime(payload.date, "%Y-%m-%d").date(),
            note=payload.note or "National Holiday",
            is_national=payload.is_national if payload.is_national is not None else True,
            client_id=user.client_id,
            created_at=datetime.now(),
        )
        db.add(new_holiday)
        db.commit()
        return "oke"
    except Exception as e:
        print(f"Error in create_data_national_holiday: {e}")
        raise ValueError(f"Error in create_data_national_holiday: {e}")
    
async def delete_data_national_holiday(
    db: Session,
    national_holiday_id: int,
    user: User,
):
    """
    This function is used to delete a national holiday record.
    """
    try:
        # Fetch the existing holiday record
        existing_holiday = db.query(NationalHoliday).filter(
            NationalHoliday.id == national_holiday_id,
            NationalHoliday.isact==True,
        ).first()

        if not existing_holiday:
            raise ValueError("National holiday not found.")

        # Mark the record as inactive (soft delete)
        existing_holiday.isact = False
        existing_holiday.updated_at = datetime.now()
        db.add(existing_holiday)
        db.commit()
        return "oke"
    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in delete_data_national_holiday: {e}")
        raise ValueError(f"Error in delete_data_national_holiday: {e}")


async def get_data_national_holiday_by_id(
    db: Session,
    national_holiday_id: str,
    user: User,
) -> DataNationalHoliday:
    """
    This function is used to get data national holiday filtered by client_id.
    This function will return a list of national holiday data.
    This function needs to be fast and efficient.
    """
    try:
        query= db.query(NationalHoliday).filter(
            NationalHoliday.client_id == user.client_id,
            NationalHoliday.isact == True,
            NationalHoliday.id == national_holiday_id
        )
        national_holidays = query.first()
        if not national_holidays:
            return DataNationalHoliday().model_dump()
        else:
            result = DataNationalHoliday(
                id=national_holidays.id,
                name=national_holidays.name,
                date=national_holidays.date.strftime("%Y-%m-%d") if national_holidays.date else None,
                note=national_holidays.note,
                is_national=national_holidays.is_national,
            ).model_dump()
            return result
    except ValueError as ve:    
        raise ve
    except Exception as e:
        print(f"Error in get_data_national_holiday_by_id: {e}")
        raise ValueError(f"Error in get_data_national_holiday_by_id")

async def get_data_national_holiday(
    db:Session,
    user: User,
) -> List[DataNationalHoliday]:
    """
    This function is used to get data national holiday filtered by client_id.
    This function will return a list of national holiday data.
    This function needs to be fast and efficient.
    This filtered by role if role == 2 will get their client
    """
    try:
        # Query the NationalHoliday table for the given client_id and isact == True

        if user.roles[0].id == 2:
            # Client role
            query = db.query(NationalHoliday).filter(
                NationalHoliday.client_id == user.client_id,
                NationalHoliday.isact == True,
            )
        elif user.roles[0].id == 1:
            # Super Admin role
            query = db.query(NationalHoliday).filter(
                NationalHoliday.client_id == user.client_id,
                NationalHoliday.isact == True,
            )
        else:
            # Admin role
            query = db.query(NationalHoliday).filter(
                NationalHoliday.client_id == 0,
                NationalHoliday.isact == True,
            )
        
        national_holidays = query.all()

        if not national_holidays:
            return [
                DataNationalHoliday()
            ]

        # Map the results to the DataNationalHoliday schema
        result = [
            DataNationalHoliday(
                id=holiday.id,
                name=holiday.name,
                date=holiday.date.strftime("%Y-%m-%d") if holiday.date else None,
                note=holiday.note,
                is_national=holiday.is_national,
            ).model_dump()
            for holiday in national_holidays
        ]

        return result
    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in get_data_national_holiday: {e}")
        raise ValueError(f"Error in get_data_national_holiday")

async def edit_national_holiday(
    db: Session,
    payload: DataHolidayRequest,
    id: str,
    user: User,
):
    """
    Optimized function to add or update national holiday data in bulk.
    """
    try:
        # Fetch existing holidays in a single query
        existing_holidays = db.query(NationalHoliday).filter(
            NationalHoliday.client_id == user.client_id,
            NationalHoliday.id == id,
            NationalHoliday.isact==True,
        ).first()

        if not existing_holidays:
            raise ValueError("No existing national holidays found for the given client_id.")
        # Update existing holiday
        existing_holidays.name = payload.name or existing_holidays.name
        existing_holidays.date = datetime.strptime(payload.date, "%Y-%m-%d").date() if payload.date else existing_holidays.date
        existing_holidays.note = payload.note or existing_holidays.note
        existing_holidays.is_national = payload.is_national if payload.is_national is not None else existing_holidays.is_national
        existing_holidays.updated_at = datetime.now()
        db.add(existing_holidays)
        # Commit the transaction
        db.commit()

        return {"message": "National holiday updated successfully."}
    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in edit_national_holiday_list: {e}")
        raise ValueError(f"Error in edit_national_holiday_list: {e}")