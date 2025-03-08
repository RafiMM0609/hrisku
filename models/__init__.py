from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from settings import (
    MYSQL
)
Base = declarative_base()

SUPABASE_URL = MYSQL

# Buat engine SQLAlchemy
engine = create_engine(f"{MYSQL}")

# Buat sesi database
SessionLocal = sessionmaker(bind=engine)

# Cek koneksi
try:
    with engine.connect() as connection:
        print("Connected to Supabase!")
except Exception as e:
    print(f"Failed to connect sync: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# base for model
Base = declarative_base()

from models.UserRole import UserRole
# from models.User import User
# from models.Permission import Permission
# from models.Role import Role