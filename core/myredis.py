import redis
from pydantic import BaseModel
from settings import REDIS_HOST, REDIS_PORT

# Inisialisasi koneksi Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1)

# Cek koneksi
try:
    redis_client.ping()
    print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError:
    print(f"Failed to connect to Redis at {REDIS_HOST}:{REDIS_PORT}")

class MenuData(BaseModel):
    id: int
    name: str
    description: str
    price: float

async def get_data_with_cache(key: str, fetch_function, model: BaseModel, ttl: int = 30, *args, **kwargs):
    """
    Mengambil data dari cache, jika tidak ada di cache, ambil dari sumber utama dan simpan di cache.

    :param key: Kunci untuk data di cache
    :param fetch_function: Fungsi untuk mengambil data dari sumber utama (misal, database)
    :param model: Pydantic model untuk validasi data
    :param ttl: Time to Live untuk data di cache (default: 60 detik)
    :param args: Argumen tambahan untuk fungsi fetch_function
    :param kwargs: Keyword argumen tambahan untuk fungsi fetch_function
    :return: Data yang diminta dalam bentuk model Pydantic
    """
    # Periksa cache
    data = redis_client.get(key)
    if data:
        return model.parse_raw(data).model_dump()  # Kembalikan data dari cache sebagai Pydantic model
    
    # Ambil data dari sumber utama
    data = await fetch_function(*args, **kwargs)

    # Validasi dan simpan di cache dengan TTL
    validated_data = model.parse_obj(data)
    redis_client.set(key, validated_data.json(), ex=ttl)
    
    return validated_data.model_dump()

def fetch_from_db(menu_id):
    """
    Fungsi contoh untuk mengambil data dari database.

    :param menu_id: ID dari menu yang diminta
    :return: Data yang diambil dari database dalam bentuk dictionary
    """
    # Contoh logika pengambilan data dari database
    # Sesuaikan dengan logika pengambilan data dari database Anda
    # Misalnya menggunakan SQLAlchemy, Django ORM, dll.
    return {
        "id": menu_id,
        "name": "Pizza",
        "description": "Delicious cheese pizza",
        "price": 9.99
    }

# Contoh penggunaan
if __name__ == "__main__":
    menu_id = 1
    cache_key = f"menu:{menu_id}"

    # Ambil data dengan cache
    menu_data = get_data_with_cache(cache_key, fetch_from_db, MenuData, ttl=60, menu_id=menu_id)
    print(menu_data)