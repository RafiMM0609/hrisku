from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Gunakan asyncpg untuk koneksi async
SUPABASE_URL = "postgresql+asyncpg://postgres.livlimcygmeebknjkbuq:Anton191969#123@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

# Buat engine async
async_engine = create_async_engine(SUPABASE_URL, echo=True)

# Buat session async
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


# Cek koneksi
# try:
#     with async_engine.connect() as connection:
#         print("Connected to Supabase!")
# except Exception as e:
#     print(f"Failed to connect  async: {e}")

# Dependency untuk mendapatkan session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session  # Gunakan yield agar session otomatis ditutup setelah digunakan

# Ganti dengan Supabase database URL Anda
SUPABASE_URL = "postgresql://postgres.livlimcygmeebknjkbuq:Anton191969#123@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
# SUPABASE_URL = "postgresql://postgres:Anton191969#123@db.livlimcygmeebknjkbuq.supabase.co:5432/postgres"

# Buat engine SQLAlchemy
engine = create_engine(SUPABASE_URL)

# Buat sesi database
SessionLocal = sessionmaker(bind=engine)

# Cek koneksi
try:
    with engine.connect() as connection:
        print("Connected to Supabase!")
except Exception as e:
    print(f"Failed to connect sync: {e}")

def sync_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()