import redis
import os
from settings import (
REDIS_HOST,
REDIS_PORT,
)

# Inisialisasi koneksi Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Cek koneksi
try:
    redis_client.ping()
    print("Connected to Redis")
except redis.ConnectionError:
    print("Failed to connect to Redis")