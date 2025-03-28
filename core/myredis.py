import redis
import os
from pydantic import BaseModel
from settings import REDIS_HOST, REDIS_PORT

# Inisialisasi koneksi Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Cek koneksi
try:
    redis_client.ping()
    print("Connected to Redis")
except redis.ConnectionError:
    print("Failed to connect to Redis")

class MenuData(BaseModel):
    id: int
    name: str
    description: str
    price: float

def get_data_with_cache(key: str, fetch_function, model: BaseModel, ttl: int = 60):
    """
    Mengambil data dari cache, jika tidak ada di cache, ambil dari sumber utama dan simpan di cache.

    :param key: Kunci untuk data di cache
    :param fetch_function: Fungsi untuk mengambil data dari sumber utama (misal, API)
    :param model: Pydantic model untuk validasi data
    :param ttl: Time to Live untuk data di cache (default: 60 detik)
    :return: Data yang diminta dalam bentuk model Pydantic
    """
    # Periksa cache
    data = redis_client.get(key)
    if data:
        return model.parse_raw(data)  # Kembalikan data dari cache sebagai Pydantic model
    
    # Ambil data dari sumber utama
    data = fetch_function()
    
    # Validasi dan simpan di cache dengan TTL
    validated_data = model.parse_obj(data)
    redis_client.set(key, validated_data.json(), ex=ttl)
    
    return validated_data

def fetch_from_api():
    """
    Fungsi contoh untuk mengambil data dari API.

    :return: Data yang diambil dari API dalam bentuk dictionary
    """
    # Contoh data dari API
    return {
        "id": 1,
        "name": "Pizza",
        "description": "Delicious cheese pizza",
        "price": 9.99
    }

# Contoh penggunaan
if __name__ == "__main__":
    cache_key = "menu:1"

    # Ambil data dengan cache
    menu_data = get_data_with_cache(cache_key, fetch_from_api, MenuData)
    print(menu_data)