import redis
import os


# Inisialisasi koneksi Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

# Cek koneksi
try:
    redis_client.ping()
    print("Connected to Redis")
except redis.ConnectionError:
    print("Failed to connect to Redis")