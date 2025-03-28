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

def get_data_with_cache(key, fetch_function, ttl=60):
    """
    Mengambil data dari cache, jika tidak ada di cache, ambil dari sumber utama dan simpan di cache.

    :param key: Kunci untuk data di cache
    :param fetch_function: Fungsi untuk mengambil data dari sumber utama (misal, database)
    :param ttl: Time to Live untuk data di cache (default: 60 detik)
    :return: Data yang diminta
    """
    # Periksa cache
    data = redis_client.get(key)
    if data:
        return data.decode('utf-8')  # Kembalikan data dari cache
    
    # Ambil data dari sumber utama
    data = fetch_function(key)
    
    # Simpan di cache dengan TTL
    redis_client.set(key, data, ex=ttl)
    
    return data

def fetch_from_db(key):
    """
    Fungsi contoh untuk mengambil data dari database (sumber utama).

    :param key: Kunci untuk data yang diminta
    :return: Data yang diambil dari database
    """
    # Simulasi pengambilan data dari database
    return "fetched_data_for_" + key

# Contoh penggunaan
if __name__ == "__main__":
    data = get_data_with_cache('example_key', fetch_from_db)
    print(data)