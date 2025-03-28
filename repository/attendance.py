from typing import Optional, List, Type
from math import ceil, radians, sin, cos, sqrt, atan2  # Add these imports for Haversine formula
import secrets
from sqlalchemy import select, func, distinct, or_, and_, case  # Added and_ import
from sqlalchemy.orm import Session, aliased
from models.User import User
from models.Role import Role
from models import SessionLocal
from models.Attendance import Attendance
from models.ShiftSchedule import ShiftSchedule
from models.LeaveTable import LeaveTable
from models.ClientOutlet import ClientOutlet
from models.TimeSheet import TimeSheet
from datetime import datetime, timedelta, time
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile

