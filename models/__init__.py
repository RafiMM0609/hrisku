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

# Konfigurasi optimal connection pool
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_size=20,         # Jumlah koneksi tetap dalam pool
    max_overflow=30,      # Tambahan koneksi saat penuh
    pool_recycle=1800,    # Recycle koneksi tiap 30 menit
    pool_timeout=10       # Timeout menunggu koneksi
)

# Create database session
# SessionLocal = sessionmaker(bind=engine)
SessionLocal = sessionmaker(bind=engine)
# Check connection
try:
    with engine.connect() as connection:
        print("Connected to MySQL!")
except Exception as e:
    print(f"Failed to connect sync: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from models.UserRole import UserRole