# HRIS-HRIS

# how to run?

- first
- bismillah
- make sure sudah terinstall python
- do it for build venv
```
python3 -m venv venv
```
- then do it to activate venv
```
source venv/bin/activate
```
- then do it to install all dependency
```
pip install -r requirements.txt
```
- then run it
```
uvicorn main:app
```


# Notes for server configuration
- Sesuaikan pool_recycle agar lebih kecil dari wait_timeout.
```
SHOW VARIABLES LIKE 'wait_timeout';
```