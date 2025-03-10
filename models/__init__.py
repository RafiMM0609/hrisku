from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from settings import (
    DB_HOST,
    DB_NAME,
    DB_PASS,
    DB_PORT,
    DB_USER
)
Base = declarative_base()

# create SQLAlchemy engine
engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


# Create database session
SessionLocal = sessionmaker(bind=engine)

# Check connection
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