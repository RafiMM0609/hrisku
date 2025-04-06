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
    EditDataHolidayRequest
)


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

        # Commit the transaction
        db.commit()
    except Exception as e:
        print(f"Error in create_update_national_holiday: {e}")
        raise ValueError(f"Error in create_update_national_holiday: {e}")
    finally:
        db.close()

async def get_data_national_holiday(
    db:Session,
    client_id: str,
) -> List[DataNationalHoliday]:
    """
    This function is used to get data national holiday filtered by client_id.
    This function will return a list of national holiday data.
    This function needs to be fast and efficient.
    """
    try:
        # Query the NationalHoliday table for the given client_id and isact == True
        national_holidays = db.query(NationalHoliday).filter(
            NationalHoliday.client_id == client_id,
            NationalHoliday.isact == True
        ).all()

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

async def add_national_holiday(
    payload: DataHolidayRequest,
    client_id: int,
    user: User,
):
    """
    This function is used to add or update national holiday data.
    If the `id` is provided, it updates the existing record.
    Otherwise, it creates a new record.
    """
    db: Session = SessionLocal()
    try:
        # Check if the holiday already exists using the provided `id`
        existing_holiday = None
        if payload.id:
            existing_holiday = db.query(NationalHoliday).filter(
                NationalHoliday.id == payload.id,
                NationalHoliday.client_id == client_id,
            ).first()

        if existing_holiday:
            # Update the existing holiday record
            existing_holiday.name = payload.name or existing_holiday.name
            existing_holiday.date = datetime.strptime(payload.date, "%Y-%m-%d").date() if payload.date else existing_holiday.date
            existing_holiday.note = payload.note or existing_holiday.note
            existing_holiday.is_national = payload.is_national if payload.is_national is not None else existing_holiday.is_national
            existing_holiday.updated_at = datetime.now()
        else:
            # Create a new NationalHoliday record
            new_holiday = NationalHoliday(
                name=payload.name,
                date=datetime.strptime(payload.date, "%Y-%m-%d").date(),
                note=payload.note or "National Holiday",
                is_national=payload.is_national if payload.is_national is not None else True,
                client_id=client_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.add(new_holiday)

        # Commit the transaction
        db.commit()

        return {"message": "National holiday added or updated successfully."}
    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in add_national_holiday: {e}")
        raise ValueError(f"Error in add_national_holiday: {e}")
    finally:
        db.close()

async def edit_national_holiday_list(
    db: Session,
    list_payload: EditDataHolidayRequest,
    client_id: str,
):
    """
    Optimized function to add or update national holiday data in bulk.
    """
    try:
        # Extract IDs from the payload
        payload_ids = [payload.id for payload in list_payload.data if payload.id]

        # Fetch existing holidays in a single query
        existing_holidays = db.query(NationalHoliday).filter(
            NationalHoliday.client_id == client_id,
            NationalHoliday.id.in_(payload_ids),
            NationalHoliday.isact==True,
        ).all()
        existing_holidays_map = {holiday.id: holiday for holiday in existing_holidays}

        # Prepare new and updated records
        new_holidays = []
        for payload in list_payload.data:
            if payload.id and payload.id in existing_holidays_map:
                # Update existing holiday
                holiday = existing_holidays_map[payload.id]
                holiday.name = payload.name or holiday.name
                holiday.date = datetime.strptime(payload.date, "%Y-%m-%d").date() if payload.date else holiday.date
                holiday.note = payload.note or holiday.note
                holiday.is_national = payload.is_national if payload.is_national is not None else holiday.is_national
                holiday.updated_at = datetime.now()
                db.add(holiday)
            else:
                # Create new holiday
                new_holidays.append(NationalHoliday(
                    name=payload.name,
                    date=datetime.strptime(payload.date, "%Y-%m-%d").date(),
                    note=payload.note or "National Holiday",
                    is_national=payload.is_national if payload.is_national is not None else True,
                    client_id=client_id,
                    created_at=datetime.now(),
                ))

        # Bulk insert new holidays
        if new_holidays:
            db.bulk_save_objects(new_holidays)

        # Commit the transaction
        db.commit()

        return {"message": "National holidays added or updated successfully."}
    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in add_national_holiday_list: {e}")
        raise ValueError(f"Error in add_national_holiday_list: {e}")