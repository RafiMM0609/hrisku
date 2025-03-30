
import base64 as b64
from io import BytesIO
import os
from re import search
from shutil import move, copyfile
from typing import Optional, Tuple, List
from datetime import datetime
from fastapi import BackgroundTasks, Response, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from minio import Minio, S3Error
from minio.datatypes import Object
# from core.img_converter import img_to_base64
from settings import (
    FILE_STORAGE_ADAPTER,
    LOCAL_PATH,
    MINIO_BUCKET,
    MINIO_ENPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    BACKEND_URL,
    TZ,
)
from datetime import timedelta
import io
from zipfile import ZipFile
import re
from core.security import generate_hash_lisensi
import asyncio

# Download File Return Bytes Stream

def download_file_to_bytes(
    path:str,
):
    response = minio_client.get_object(MINIO_BUCKET, path)
    image_data = response.read()
    response.close()
    response.release_conn()
    return image_data
    

# Using Local file system
async def upload_file_to_tmp(
    upload_file: UploadFile, filename: Optional[str] = None
) -> Tuple[str, str]:
    contents = await upload_file.read()
    if filename == None:
        now = datetime.now().strftime("%Y%m%d%H%M%S%s")
        full_file_path = f"./tmp/{now}_{upload_file.filename}"
        db_file_path = f"{now}_{upload_file.filename}"
    else:
        full_file_path = f"./tmp/{filename}"
        db_file_path = filename
    with open(full_file_path, "wb") as f:
        f.write(contents)
    return (db_file_path, full_file_path)


async def upload_file_to_local(
    upload_file: UploadFile, path: str, folder: str = ""
) -> str:
    contents = await upload_file.read()
    full_path = f"{folder}/{path}"
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(contents)
    return path


def download_file_from_local(
    path: str,
    folder: str,
    filename: Optional[str] = None,
    media_type: str = "application/octet-stream",
) -> Optional[FileResponse]:
    if filename == None:
        # get filename from path if filename = None
        if search(r"\/", path) != None:
            # there is / in path
            # example: folder/file.txt => file.txt
            filename = path.split("/")[-1]
        else:
            # there is no / in path
            filename = path

    path = f"{folder}/{path}"
    if os.path.exists(path=path):
        return FileResponse(path=path, media_type=media_type, filename=filename)
    else:
        return None


def is_file_exists_in_local(path: str, folder="./") -> bool:
    path = f"{folder}/{path}"
    return os.path.exists(path=path)


def move_file_in_local(source: str, destination: str, folder="./"):
    move(f"{folder}/{source}", f"{folder}/{destination}")


def move_file_in_local_v2(source: str, destination: str):
    move(source, destination)


def copy_file_to_local(source: str, destination: str):
    copyfile(source, destination)


def delete_file_in_local(folder: str, path: str) -> bool:
    full_file_path = f"{folder}/{path}"
    if os.path.exists(full_file_path):
        os.remove(full_file_path)
        return True
    else:
        return False


def delete_file_in_tmp(path: str):
    full_path = f"./tmp/{path}"
    if os.path.exists(full_path):
        os.remove(full_path)


def clean_tmp():
    TEMP_FOLDER = "./tmp"
    for filename in os.listdir(TEMP_FOLDER):
        if filename != ".gitkeep":
            path_delete = os.path.join(TEMP_FOLDER, filename)
            os.unlink(path_delete)


def local_to_local(source: str, destination: str, folder: str = ""):
    full_path = f"{folder}/{destination}"
    move(source, full_path)


# Using Minio
minio_client = Minio(
    MINIO_ENPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def is_file_exists_in_minio(bucket: str, filepath: str) -> bool:
    try:
        minio_client.get_object(bucket_name=bucket, object_name=filepath)
        return True
    except S3Error as e:
        return False


def upload_file_from_path_to_minio(
        local_path: str, 
        minio_path: str,
        bucket: Optional[str]=MINIO_BUCKET, 
        ):
    found = minio_client.bucket_exists(bucket_name=bucket)
    if not found:
        minio_client.make_bucket(bucket_name=bucket)

    minio_client.fput_object(
        bucket_name=bucket, object_name=minio_path, file_path=local_path
    )


def download_file_to_path_from_minio(
    bucket: str, minio_path: str, local_path: str
) -> Optional[Object]:
    try:
        x = minio_client.fget_object(
            bucket_name=bucket, file_path=local_path, object_name=minio_path
        )
    except S3Error as e:
        return None
    return x


async def upload_file_to_minio(upload_file: UploadFile, bucket: str, path: str) -> str:
    """
    return minio_path
    """
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    relative_path, full_path = await upload_file_to_tmp(
        upload_file=upload_file, filename=f"{now}.bak"
    )
    try:
        upload_file_from_path_to_minio(
            bucket=bucket, local_path=full_path, minio_path=path
        )
        delete_file_in_tmp(path=relative_path)
    except Exception as e:
        delete_file_in_tmp(path=relative_path)
        raise Exception(e)
    return path

# async def upload_zip(zip_file: UploadFile, username: str):
#     try:
#         data_return=[]
#         zip_contents = await zip_file.read()
#         with ZipFile(io.BytesIO(zip_contents)) as zip:
#             zip_file_names = zip.namelist()
#             for name in zip_file_names:
#                 object_return={}
#                 with zip.open(name) as file:
#                     file_content = file.read()
#                     temp_file_path = f"/tmp/{name}"
#                     with open(temp_file_path, "wb") as temp_file:
#                         temp_file.write(file_content)
#                     now = datetime.now().strftime("%Y-%m-%d%H-%M-%S")
#                     file_path=f'data-tkt/{username}{now}{name}'
#                     minio_client.fput_object(
#                         MINIO_BUCKET,
#                         file_path,
#                         temp_file_path
#                     )
#                     os.remove(temp_file_path)
#                     # text = "License (6).lic"
#                     match = re.search(r'\((\d+)\)\.lic', name)
#                     # if match:
#                     #     print(match.group(1))
#                     object_return['file_name']=name
#                     object_return['lisensi_hash']=generate_hash_lisensi(str(file_content))
#                     object_return['file_path']=file_path
#                     object_return['file_maping']=match.group(1)
#                     data_return.append(object_return)
#         return data_return
#     except Exception as e:
#         raise ValueError(e)





async def upload_zip(zip_file: UploadFile, username: str):
    try:
        data_return = []
        zip_contents = await zip_file.read()
    
        with ZipFile(io.BytesIO(zip_contents)) as zip:
            zip_file_names = zip.namelist()
            
            async def process_file(name):
                object_return = {}
                with zip.open(name) as file:
                    file_content = file.read()
                    now = datetime.now().strftime("%Y-%m-%d%H-%M-%S")
                    file_path = f'data/{username}{now}{name}'
                    
                    # Streaming langsung ke MinIO
                    file_stream = BytesIO(file_content)
                    file_size = len(file_content)
                    
                    minio_client.put_object(
                        MINIO_BUCKET,
                        file_path,
                        file_stream,
                        file_size
                    )
                    
                    match = re.search(r'\((\d+)\)\.lic', name)
                    object_return['file_name'] = name
                    object_return['lisensi_hash'] = generate_hash_lisensi(str(file_content))
                    object_return['file_path'] = file_path
                    object_return['file_maping'] = match.group(1) if match else None
                return object_return

            # Proses file secara asinkron
            tasks = [asyncio.create_task(process_file(name)) for name in zip_file_names]
            data_return = await asyncio.gather(*tasks)

        return data_return
    except Exception as e:
        raise ValueError(str(e))


async def upload_file_to_minio_directly(upload_file: UploadFile, bucket: str, path: str) -> str:
    """
    Upload directly to MinIO without saving to temporary storage.
    """
    try:
        # Use the file directly for upload
        file_content = await upload_file.read()
        file_size = len(file_content)
        file_obj = io.BytesIO(file_content)
        minio_client.put_object(
            bucket_name=bucket,
            object_name=path,
            data=file_obj,
            length=file_size,  # Pass the size of the file
            content_type=upload_file.content_type  # Optionally set the content type
        )
        
    except Exception as e:
        # Handle any exceptions during the upload
        raise Exception(f"Failed to upload to MinIO: {e}")
    
    return path

def download_file_from_minio(
    bucket: str,
    minio_path: str,
    filename: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None,
    media_type: str = "application/octet-stream",
) -> Optional[FileResponse]:
    """
    download file from minio then return fastapi.responses.FileResponse or None
    """
    if filename == None:
        # get filename from minio_path if filename = None
        if search(r"\/", minio_path) != None:
            # there is / in minio_path
            # example: folder/file.txt => file.txt
            filename = minio_path.split("/")[-1]
        else:
            # there is no / in minio_path
            filename = minio_path

    # download to tmp folder
    download_path = f"./tmp/{filename}"
    file_object = download_file_to_path_from_minio(
        bucket=bucket, local_path=download_path, minio_path=minio_path
    )
    if file_object != None:
        if background_tasks != None:
            background_tasks.add_task(delete_file_in_tmp, filename)
        return FileResponse(
            path=download_path, media_type=media_type, filename=filename
        )
    else:
        return None


def preview_file_from_minio(bucket: str,
                            filepath: str,
                            media_type: str = "application/octet-stream"):
    try:
        file_stream = minio_client.get_object(bucket, filepath)
        return StreamingResponse(BytesIO(file_stream.read()), media_type=media_type)
    except Exception as e:
        return Response(content=str(e), status_code=500)


def delete_file_from_minio(bucket: str, filename: str):
    minio_client.remove_object(bucket_name=bucket, object_name=filename)


def move_file_minio(bucket: str, source: str, destination: str):
    now = datetime.now().strftime("%Y%m%d%H%M%S%s")
    download_file_to_path_from_minio(
        bucket=bucket, minio_path=source, local_path=f"./tmp/{now}.bak"
    )
    upload_file_from_path_to_minio(
        bucket=bucket, local_path=f"./tmp/{now}.bak", minio_path=destination
    )
    delete_file_from_minio(bucket=bucket, filename=source)


def remove_bucket_in_minio(bucket: str):
    found = minio_client.bucket_exists(bucket_name=bucket)
    if not found:
        return
    all_files_in_bucket = minio_client.list_objects(bucket_name=bucket, recursive=True)
    all_objects_name_in_bucket = [x.object_name for x in all_files_in_bucket]
    for item in all_objects_name_in_bucket:
        minio_client.remove_object(bucket_name=bucket, object_name=item)
    minio_client.remove_bucket(bucket_name=bucket)


def minio_url_from_path(filepath: str):
    try:
        file = minio_client.get_presigned_url(
            method="GET",
            bucket_name=MINIO_BUCKET,
            object_name=f"data/{filepath}",
            expires=timedelta(hours=1)
        )
        return file
    except Exception as e:
        return None


# Abstraction for upload and download file
async def upload_file(upload_file: UploadFile, path: str) -> str:
    print('Start upload file in backgorund')
    print(FILE_STORAGE_ADAPTER)
    if FILE_STORAGE_ADAPTER == "local":
        path = await upload_file_to_local(
            upload_file=upload_file, folder=LOCAL_PATH, path=f"{path}"
        )
    elif FILE_STORAGE_ADAPTER == "minio":
        path = await upload_file_to_minio(
            upload_file=upload_file, bucket=MINIO_BUCKET, path=path
        )
    print(f'Success with {path}')
    return path


def download_file(
    path: str,
    filename: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None,
    media_type: str = "application/octet-stream",
) -> Optional[FileResponse]:
    if FILE_STORAGE_ADAPTER == "local":
        file_response = download_file_from_local(
            folder=LOCAL_PATH, path=path, filename=filename, media_type=media_type
        )
    elif FILE_STORAGE_ADAPTER == "minio":
        file_response = download_file_from_minio(
            bucket=MINIO_BUCKET,
            minio_path=path,
            filename=filename,
            media_type=media_type,
            background_tasks=background_tasks,
        )
    return file_response


def is_file_exists(path: str) -> bool:
    is_exists = False
    if FILE_STORAGE_ADAPTER == "local":
        is_exists = is_file_exists_in_local(folder=LOCAL_PATH, path=path)
    elif FILE_STORAGE_ADAPTER == "minio":
        is_exists = is_file_exists_in_minio(bucket=MINIO_BUCKET, filepath=path)
    return is_exists


def move_file(source: str, destination: str):
    if FILE_STORAGE_ADAPTER == "local":
        move_file_in_local(folder=LOCAL_PATH, source=source, destination=destination)
    elif FILE_STORAGE_ADAPTER == "minio":
        move_file_minio(bucket=MINIO_BUCKET, source=source, destination=destination)


def delete_file(path: str):
    if FILE_STORAGE_ADAPTER == "local":
        delete_file_in_local(folder=LOCAL_PATH, path=path)
    elif FILE_STORAGE_ADAPTER == "minio":
        delete_file_from_minio(bucket=MINIO_BUCKET, filename=path)


def local_to_adapter(local_source: str, destination: str):
    if FILE_STORAGE_ADAPTER == "local":
        local_to_local(source=local_source, destination=destination, folder=LOCAL_PATH)
    elif FILE_STORAGE_ADAPTER == "minio":
        upload_file_from_path_to_minio(
            bucket=MINIO_BUCKET, local_path=local_source, minio_path=destination
        )


def adapter_to_local(adapter_path: str, local_path: str):
    if FILE_STORAGE_ADAPTER == "local":
        copy_file_to_local(
            source=f"{LOCAL_PATH}/{adapter_path}", destination=local_path
        )
    elif FILE_STORAGE_ADAPTER == "minio":
        download_file_to_path_from_minio(
            bucket=MINIO_BUCKET, minio_path=adapter_path, local_path=local_path
        )


def adapter_img_to_base_64(
    adapter_path: str,
    background_tasks: Optional[BackgroundTasks] = None
) -> str:
    tmp_filename = adapter_path.split("/")[-1]
    if FILE_STORAGE_ADAPTER == "local":
        copy_file_to_local(
            source=f"{LOCAL_PATH}/{adapter_path}", destination=f"./tmp/{tmp_filename}"
        )
    elif FILE_STORAGE_ADAPTER == "minio":
        download_file_to_path_from_minio(
            bucket=MINIO_BUCKET,
            minio_path=adapter_path,
            local_path=f"./tmp/{tmp_filename}",
        )

    # This commented code below is not working
    # i think the function `img_to_base64` is problematic
    # it also causes a glitch to the transparency of a .png file
    # base64 = img_to_base64(local_path=f"./tmp/{tmp_filename}")

    # I don't want to touch the function, therefore i implemented a new way
    with open(f"./tmp/{tmp_filename}", "rb") as image_file:
        image_data = image_file.read()
        base64 = b64.b64encode(image_data).decode("utf-8")

    if background_tasks is not None:
        background_tasks.add_task(delete_file_in_tmp, tmp_filename)

    return base64

def generate_link_download(file_name:str):
    try:
        if FILE_STORAGE_ADAPTER == "local":
            # url = 'http://127.0.0.1:8000/minio/download/?minio_path='
            url = f'{BACKEND_URL}/minio/download/?minio_path='
            return url + file_name
        elif FILE_STORAGE_ADAPTER == "minio":
            presigned_url = minio_client.presigned_get_object(
                MINIO_BUCKET, file_name, expires=timedelta(hours=48)
            )
            return presigned_url
    except Exception as e:
        return None
    
def download_list_file(
    list_path: List[str],
) -> Optional[List[str]]:
    list_download_path = []
    if FILE_STORAGE_ADAPTER == "local":
        for path in list_path:
            filepath = f"{LOCAL_PATH}/{path}"
            if os.path.exists(path=filepath):
                list_download_path.append(filepath)

    elif FILE_STORAGE_ADAPTER == "minio":
        for path in list_path:
            if search(r"\/", path) != None:
                filename = path.split("/")[-1]
            else:
                filename = path

            download_path = f"./tmp/{filename}"
            file_object = download_file_to_path_from_minio(
                bucket=MINIO_BUCKET, local_path=download_path, minio_path=path
            )
            if file_object != None:
                list_download_path.append(download_path)

    return list_download_path

async def create_zip_from_list_file(
    list_path: List[str], 
    zip_name: str
) -> Optional[str]:
    try:
        with ZipFile(f"./tmp/{zip_name}", "w", ) as zip:
            for path in list_path:
                zip.write(path, os.path.basename(path))
        return f"./tmp/{zip_name}"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    
async def upload_file_local_to_minio(local_path: str, minio_path: str) -> Optional[str]:
    try:
        upload_file_from_path_to_minio(
            bucket=MINIO_BUCKET, local_path=local_path, minio_path=minio_path
        )
        return "success"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    
def delete_file_from_local(path: str):
    if os.path.exists(path):
        os.remove(path)
    
# class ZipExtFileUploadFile(UploadFile):
#     def __init__(self, zip_ext_file: 'zipfile.ZipExtFile', filename: str, content_type: str):
#         self._zip_ext_file = zip_ext_file
#         self.filename = filename
#         self._content_type = content_type

#     async def read(self, size: int = -1) -> bytes:
#         return self._zip_ext_file.read(size)

#     async def seek(self, offset: int, whence: int = 0) -> None:
#         self._zip_ext_file.seek(offset, whence)

#     async def close(self) -> None:
#         self._zip_ext_file.close()

#     @property
#     def file(self):
#         return self._zip_ext_file

#     @property
#     def content_type(self):
#         return self._content_type
    

class ZipExtFileUploadFile(UploadFile):
    def __init__(self, zip_ext_file: 'zipfile.ZipExtFile', filename: str, content_type: str):
        self._zip_ext_file = zip_ext_file
        self.filename = filename
        self._content_type = content_type

    async def read(self, size: int = -1) -> bytes:
        return self._zip_ext_file.read(size)  # Read the file in one pass

    async def close(self) -> None:
        self._zip_ext_file.close()

    @property
    def file(self):
        return self._zip_ext_file

    @property
    def content_type(self):
        return self._content_type