import os
from core.utils import str_to_bool

if os.environ.get("ENVIRONTMENT") != "prod":
    from dotenv import load_dotenv

    load_dotenv()
# MYSQL=os.environ.get("MYSQL", "")
DB_HOST=os.environ.get("DB_HOST", "")
DB_PORT=os.environ.get("DB_PORT", "")
DB_NAME=os.environ.get("DB_NAME", "")
DB_USER=os.environ.get("DB_USER", "")
DB_PASS=os.environ.get("DB_PASS", "")
LOCAL_PATH = os.environ.get("LOCAL_PATH", "./storage")
FILE_STORAGE_ADAPTER = os.environ.get("FILE_STORAGE_ADAPTER", "minio")
if not FILE_STORAGE_ADAPTER in ["local", "minio"]:
    raise Exception(
        "Invalid FILE_STORAGE_ADAPTER, FILE_STORAGE_ADAPTER should local or minio"
    )
# Minio
MINIO_ENPOINT = os.environ.get("MINIO_ENPOINT", "")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_SECURE = str_to_bool(os.environ.get("MINIO_SECURE", "False"))
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "ticketing")
# backend url
BACKEND_URL = os.environ.get("BACKEND_URL", "")
SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
SENTRY_TRACES_SAMPLE_RATES = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATES", 1.0))

ENVIRONTMENT = os.environ.get("ENVIRONTMENT", "dev")
SECRET_KEY='Rx5634F0waUoh8ExHsDq6lGHFbT6u2AwxEXz9UqYIRZorsGV2J15p8LUxtOb9Qx1HqZnrtlMplNaFHkkIYJEVBE6eDgIfRiVh9su'
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=720
TZ='Asia/Jakarta'
MAIL_USERNAME=os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD", "")
MAIL_FROM=os.environ.get("MAIL_FROM", "")
MAIL_PORT=os.environ.get("MAIL_PORT", "")
MAIL_SERVER=os.environ.get("MAIL_SERVER", "")
MAIL_FROM_NAME=os.environ.get("MAIL_SERVER", "")

# Redis configuration
# Use environment variable with fallback to service name for Docker
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

MAIL_TLS=False
MAIL_SSL=False
USE_CREDENTIALS=True
FE_DOMAIN='hris.com'