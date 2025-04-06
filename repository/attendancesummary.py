"""
This file need sets to user KIS (keep it simple) method
this file build to create logic CRUD for attendance summary table
"""
import calendar
from core.rafiexcel import RafiExcel, blue_fill, yellow_fill
from models import SessionLocal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, date
from models.Client import Client
from models.AttendanceSummary import AttendanceSummary
from models.Attendance import Attendance
from models.Contract import Contract
from models.ShiftSchedule import ShiftSchedule
from models.User import User
from tempfile import NamedTemporaryFile
from starlette.datastructures import UploadFile
from core.file import upload_file, upload_file_to_tmp
import io


async def create_update_attendance_summary(
    emp_id: str,
    client_id: int,
): 
    db: Session = SessionLocal()
    try:
        # Data Preparation
        today = datetime.now().date()
        # Calculate the start and end dates of the current month
        start_of_month = today.replace(day=1)
        _, last_day_of_month = calendar.monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day_of_month)
        
        # Data client
        data_client = db.query(Client).filter(
            Client.id == client_id,
            Client.isact == True
        ).first()
        if not data_client:
            print(f"Client not found for client_id: {client_id}")

        # Data contract user
        data_contract = db.query(Contract).filter(
            Contract.emp_id == emp_id,
            or_(
                Contract.start <= today,
                Contract.end >= today
            ),
            Contract.isact == True
        ).first()
        if not data_contract:
            raise ValueError(f"No active contract found for emp_id: {emp_id}")
        
        
        # Count total attendance records for the current month
        total_attendance = db.query(
            func.count(Attendance.id)
        ).filter(
            Attendance.emp_id == emp_id,
            Attendance.client_id == client_id,
            Attendance.isact == True,
            Attendance.date >= start_of_month,
            Attendance.date <= end_of_month
        ).scalar()
        
        total_workdays = await get_total_workdays_in_this_month(db, client_id, emp_id)

        # Count Monthly Paid
        basic_salary = data_client.basic_salary if data_client else 0
        if total_attendance > 17:
            monthly_paid = basic_salary
        else:
            monthly_paid = (basic_salary / 17) * total_attendance

        # Check if an attendance summary already exists for the given month_date
        existing_summary = db.query(AttendanceSummary).filter(
            AttendanceSummary.client_id == client_id,
            AttendanceSummary.emp_id == emp_id,
            AttendanceSummary.month_date == end_of_month - timedelta(days=1)
        ).first()

        if existing_summary:
            # Update the existing record
            existing_summary.total_work_days = total_workdays
            existing_summary.total_attendance = total_attendance
            existing_summary.monthly_salary = monthly_paid
            existing_summary.attendance_percentage = (total_attendance / total_workdays) * 100 if total_workdays > 0 else 0
            existing_summary.updated_at = datetime.now()
        else:
            # Create a new record
            new_attendance_summary = AttendanceSummary(
                client_id=client_id,
                emp_id=emp_id,
                contract_id=data_contract.id,
                month_date=end_of_month - timedelta(days=1),
                total_work_days=total_workdays,
                total_attendance=total_attendance,
                monthly_salary=monthly_paid,
                created_at=datetime.now(),
                attendance_percentage=(total_attendance / total_workdays) * 100 if total_workdays > 0 else 0,
            )
            db.add(new_attendance_summary)

        db.commit()
    except ValueError as ve:
        raise ve
    except Exception as e:
        print(f"Error in create_update_attendance_summary: {e}")
        raise ValueError(f"Error in create_update_attendance_summary: {e}")
    finally:
        db.close()
    
async def get_total_workdays_in_this_month(db: Session, client_id: int, emp_id: str):
    try:
        # Data Preparation
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        _, last_day_of_month = calendar.monthrange(today.year, today.month)
        end_of_month = today.replace(day=last_day_of_month)

        # Generate a list of actual date objects for the current month
        days_in_month = [
            start_of_month + timedelta(days=i)
            for i in range((end_of_month - start_of_month).days + 1)
        ]

        # Retrieve the days of the week from ShiftSchedule for the employee
        shift_days = db.query(ShiftSchedule).filter(
            ShiftSchedule.client_id == client_id,
            ShiftSchedule.emp_id == emp_id,
            ShiftSchedule.isact == True,
        ).all()

        if shift_days:
            # Map day names to weekday numbers
            day_name_to_number = {
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
                "Sunday": 6,
            }

            # Extract the days of the week from the ShiftSchedule
            workdays_in_week = {
                day_name_to_number[shift.day]
                for shift in shift_days
                if shift.day in day_name_to_number
            }

            # Count the total occurrences of each workday in the current month
            total_workdays_count = sum(
                1 for day in days_in_month if day.weekday() in workdays_in_week
            )
        else:
            total_workdays_count = 0  # Default to 0 if no shift schedule is found

        return total_workdays_count
    except Exception as e:
        print(f"Error in get_total_workdays_in_this_month: {e}")
        raise ValueError(f"Error in get_total_workdays_in_this_month: {e}")