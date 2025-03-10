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



ENVIRONTMENT = 'dev'
SECRET_KEY='Rx5634F0waUoh8ExHsDq6lGHFbT6u2AwxEXz9UqYIRZorsGV2J15p8LUxtOb9Qx1HqZnrtlMplNaFHkkIYJEVBE6eDgIfRiVh9su'
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=720
TZ='Asia/Jakarta'
MAIL_USERNAME="77f9dc002@smtp-brevo.com"
MAIL_PASSWORD="sGmcv6CT5kNIQPLd"
MAIL_FROM="mahrusrafi@gmail.com"
MAIL_PORT=587
MAIL_SERVER="smtp-relay.brevo.com"
MAIL_FROM_NAME="HRIS KU"
MAIL_TLS=False
MAIL_SSL=False
USE_CREDENTIALS=True
FE_DOMAIN='hris.com'