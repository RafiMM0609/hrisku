# from sqlalchemy import create_engine, MetaData
# from sqlalchemy.orm import sessionmaker

# # Ganti dengan Supabase database URL Anda
# # SUPABASE_URL = "postgresql://postgres.livlimcygmeebknjkbuq:Anton191969#123@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"
# SUPABASE_URL = "postgresql://postgres:Anton191969#123@db.livlimcygmeebknjkbuq.supabase.co:5432/postgres"

# # Buat engine SQLAlchemy
# engine = create_engine(SUPABASE_URL)

# # Buat sesi database
# SessionLocal = sessionmaker(bind=engine)

# # Cek koneksi
# try:
#     with engine.connect() as connection:
#         print("Connected to Supabase!")
# except Exception as e:
#     print(f"Failed to connect: {e}")
