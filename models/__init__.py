from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import logging
import time
from settings import (
    DB_HOST,
    DB_NAME,
    DB_PASS,
    DB_PORT,
    DB_USER
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# Konfigurasi optimal connection pool
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_size=20,         # Optimal untuk aplikasi medium-sized
    max_overflow=40,      # Tambahan koneksi saat penuh
    pool_recycle=1800,    # Recycle koneksi tiap 30 menit
    pool_timeout=30,      # Timeout menunggu koneksi
    pool_pre_ping=True,   # Validates connections before use
    echo=False            # Set to True for SQL debugging
)

# Add connection pool monitoring
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    logger.debug("Database connection established")

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("Database connection retrieved from pool")

# Add query execution time logging
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    if logger.level <= logging.DEBUG:
        logger.debug(f"Start executing query: {statement}")

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    execution_time_ms = round(total_time * 1000, 2)
    if execution_time_ms > 100:  # Log slow queries with WARNING level
        logger.warning(f"Slow query detected - Execution time: {execution_time_ms}ms - Query: {statement}")
    else:
        logger.info(f"Query execution time: {execution_time_ms}ms - Query: {statement[:200]}{'...' if len(statement) > 200 else ''}")

# Create database session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Validate database connection on startup
try:
    with engine.connect() as connection:
        logger.info("Successfully connected to MySQL database")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")

from models.UserRole import UserRole