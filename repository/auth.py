from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from core.security import validated_user_password, generate_hash_password, get_user_permissions
from core.utils import generate_token
from core.file import upload_file_to_local, delete_file_in_local, upload_file
from core.mail import send_reset_password_email
from models.User import User
from models.ForgotPassword import ForgotPassword
from models.UserToken import UserToken
from models.Menu import Menu
from models.Permission import Permission
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ, LOCAL_PATH
from fastapi import UploadFile
from schemas.auth import (
    MenuDict
)
# import numpy as np
# from PIL import Image
import io
import asyncio
import os
import requests
# os.environ["CUDA_VISIBLE_DEVICES"] = '-1'
# os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'
# import cv2
from schemas.auth import FirstLoginUserRequest

# backends = [
#   'opencv', 
#   'ssd', 
#   'dlib', 
#   'mtcnn', 
#   'fastmtcnn',
#   'retinaface', 
#   'mediapipe',
#   'yolov8',
#   'yunet',
#   'centerface',
# ]

# alignment_modes = [True, False]
# async def resize_image(image_path, size=(224, 224)):
#     print("ini image_path : \n",image_path)
#     img = cv2.imread(image_path)
#     resized_img = cv2.resize(img, size)
#     return resized_img
def expand_menu_tree_with_permissions(
    db: Session, root_menu: List[Menu], permissions: List[Permission]
) -> List[MenuDict]:
    if len(root_menu) == 0:
        return []
    else:
        return [
            {
                "id": y.id,
                "url": y.url,
                "name": y.name,
                "icon": y.icon,
                "is_has_child": y.is_has_child,
                "isact": y.isact,
                "is_show": y.is_show,
                "order": y.order_id if y.order_id != None else 0,
                "sub_menu": expand_menu_tree_with_permissions(
                    db=db, root_menu=y.child, permissions=permissions
                ),
            }
            for y in sorted(root_menu, key=lambda d: d.id)
            if y.isact == True
            and (
                y.permission_id in [x.id for x in permissions]
                # or y.permission_id == None
            )
        ]
def sort_menu_tree_by_order(trees: List[MenuDict]) -> List[MenuDict]:
    return [
        {
            "id": y["id"],
            "title": y["name"],
            "path": y["url"],
            "icon": y["icon"],
            "is_show": y["is_show"],
            # "is_has_child": y["is_has_child"],
            # "is_active": y["is_active"],
            # "order": y["order"],
            "sub": sort_menu_tree_by_order(y["sub_menu"]) if len(y["sub_menu"]) > 0 else False,
        }
        for y in sorted(trees, key=lambda d: d["order"])
    ]
def prune_menu_tree(trees: List[MenuDict]) -> List[MenuDict]:
    pruned_tree = []
    for tree in trees:
        if tree["is_has_child"] and len(tree["sub_menu"]) == 0:
            continue
        elif tree["is_has_child"] and len(tree["sub_menu"]) > 0:
            tree["sub_menu"] = prune_menu_tree(tree["sub_menu"])
        pruned_tree.append(tree)
    return pruned_tree
def generate_menu_tree_for_user(db: Session, user: User) -> List[MenuDict]:
    permissions = get_user_permissions(db=db, user=user)
    query = select(Menu).where(Menu.parent_id == None).order_by(Menu.id.asc())
    root_menu: List[Menu] = db.execute(query).scalars().all()
    menu_tree = expand_menu_tree_with_permissions(
        db=db, root_menu=root_menu, permissions=permissions
    )
    menu_tree = prune_menu_tree(menu_tree)
    menu_tree = sort_menu_tree_by_order(menu_tree)
    return menu_tree
async def first_login(
    db:Session,
    user: User,
    payload: FirstLoginUserRequest
):
    try:
        user.password = generate_hash_password(password=payload.password)
        user.first_login = None
        db.add(user)
        db.commit()
        return user
    except Exception as e:
        print(f"Error first login: {e}")
        raise ValueError("Error first login")
async def regis_face(
    upload_file_request:UploadFile,
    user: User,
    db: Session,
):
    try:
        file_extension = os.path.splitext(upload_file_request.filename)[1]
        file_name = os.path.splitext(upload_file_request.filename)[0]
        now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        path = await upload_file(
        upload_file=upload_file_request, path=f"/tmp/{str(file_name).replace(' ','_')}-{user.name}{now.replace(' ','_')}{file_extension}"
        )
        user.face_id = path
        db.add(user)
        db.commit()
        return "Oke"
    except Exception as e:
        print(f"Error regis face: {e}")
        raise ValueError("Error regis face")
# async def regis_face(
#     upload_file:UploadFile,
#     user: User,
#     db: Session,
# ):
#     try:
#         from deepface import DeepFace
#         file_extension = os.path.splitext(upload_file.filename)[1]
#         now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
#         path = await upload_file_to_local(
#                 upload_file=upload_file, folder=LOCAL_PATH, path=f"/tmp/face-{user.name}{now.replace(' ','_')}{file_extension}"
#             )
#         loop = asyncio.get_running_loop()
#         resized_img1 = await loop.run_in_executor(None, resize_image, f"{LOCAL_PATH}{path}")
                                                
#         # face detection
#         objs = DeepFace.analyze(
#             img_path = resized_img1, 
#             actions = ['age', 'gender', 'race', 'emotion'],
#         )
#         delete_file_in_local(folder=LOCAL_PATH, path=path)
#         print(objs)
#         path = await upload_file(
#             upload_file=upload_file, path=f"/face/face-{user.name}{now.replace(' ','_')}{file_extension}"
#         )
#         user.face_id = path
#         db.add(user)
#         db.commit()
#         return "Oke"
#     except Exception as e:
#         print(f"Error regis face: {e}")
#         raise ValueError("Error regis face")
async def get_numpy_from_minio(file_path):
    MINIO_URL = "http://localhost:9000"
    response = requests.get(f"{MINIO_URL}/{file_path}")
    if response.status_code == 200:
        image = Image.open(io.BytesIO(response.content))  # Konversi ke PIL
        image_np = np.array(image)  # Konversi ke NumPy
        
        # Jika ada alpha channel, konversi ke RGB
        if image_np.shape[-1] == 4:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
        
        return image_np
    else:
        raise ValueError("Failed to download image from MinIO")
async def get_numpy_from_upload(upload_file):
    image_bytes = await upload_file.read()  # Baca gambar sebagai bytes
    image = Image.open(io.BytesIO(image_bytes))  # Konversi ke PIL Image
    image_np = np.array(image)  # Konversi ke NumPy array
    
    # Jika gambar memiliki alpha channel (RGBA), ubah ke RGB
    if image_np.shape[-1] == 4:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
    
    return image_np
async def face(
    upload_file:UploadFile,
    user: User,
    db: Session,
):
    # from deepface import DeepFace
    # # file_extension = os.path.splitext(upload_file.filename)[1]
    # # now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    # # path = await upload_file_to_local(
    # #         upload_file=upload_file, folder=LOCAL_PATH, path=f"/tmp/face-{user.name}{now.replace(' ','_')}{file_extension}"
    # #     )
    # resized_img1 = await get_numpy_from_upload(upload_file)
    # # resized_img1 = await loop.run_in_executor(None, resize_image, f"{LOCAL_PATH}{path}")
    # # resized_img2 = await loop.run_in_executor(None, resize_image, f"{LOCAL_PATH}{user.face_id}")
    # # resized_img1 = resize_image(f"{LOCAL_PATH}{path}")
    # resized_img2 = await resize_image(f"{LOCAL_PATH}{user.face_id}")
                                            
    # #face verification
    # obj = DeepFace.verify(
    # img1_path = resized_img1, 
    # img2_path = resized_img2, 
    # detector_backend = backends[0],
    # align = alignment_modes[0],
    # )
    # # delete_file_in_local(folder=LOCAL_PATH, path=path)
    # return obj['verified']
    return "Oke"


async def check_user_status_by_email(
    db: Session,
    email: str
) -> Optional[User]:

    query = select(User).filter(
                func.lower(User.email) == email.lower(),
                User.is_active == True
            )

    user = db.execute(query).scalar()
    return user


async def get_user_by_email(
    db: Session, email: str, exclude_soft_delete: bool = False
) -> Optional[User]:
    try:
        if exclude_soft_delete == True:
            pass
            # query = select(User).filter(func.lower(User.email) == email.lower(), User.deleted_at == None)
        else:
            # why there is delete_at and is_active
            # query = select(User).filter(func.lower(User.email) == email.lower())
            query = select(User).filter(User.email == email)
        user = db.execute(query).scalar()
        if user.password == None:
            return user, True
        return user, False
    except Exception as e:
        print("Error login : ",e)
        return None, False
async def get_user_by_username(
    db: Session, username: str, exclude_soft_delete: bool = False
) -> Optional[User]:
    try:
        if exclude_soft_delete == True:
            pass
            # query = select(User).filter(func.lower(User.username) == username.lower(), User.deleted_at == None)
        else:
            # why there is delete_at and is_active
            query = select(User).filter(func.lower(User.username) == username.lower(), User.is_active == True)
        user = db.execute(query).scalar()
        return user
    except Exception as e:
        return None
    
async def delete_user_session(db: Session, user_id: str, token=str) -> str:
    try:    
        user_token = db.execute(
            select(UserToken).filter(
                UserToken.user_id == user_id,
                UserToken.token == token
            )
        ).scalar()
        user_token.is_active = False
        db.add(user_token)
        db.commit()
        return 'succes'
    except Exception as e:
        print(f"Error delete user session: {e}")
        raise ValueError(e)
    
async def create_user_session(db: Session, user_id: str, token:str) -> str:
    try:
        exist_data = db.execute(
            select(UserToken).filter(
                UserToken.emp_id == user_id,
                UserToken.token == token
            )
        ).scalar()
        if exist_data is not None:
            exist_data.is_active = True
            db.add(exist_data)
            db.commit()
        else:
            user_token = UserToken(emp_id=user_id, token=token)
            db.add(user_token)
            db.commit()
        return 'succes'
    except Exception as e:
        print(f"Error creating user session: \n {e}")
async def create_user_session_me(db: Session, user_id: str, token:str, old_token:str) -> str:
    try:
        # old_token = db.execute(
        #     select(UserToken).filter(
        #         UserToken.token == old_token,
        #         UserToken.user_id == user_id
        #     )
        # ).scalar()
        # old_token.is_active = False
        exist_data = db.execute(
            select(UserToken).filter(
                UserToken.emp_id == user_id,
                UserToken.token == token
            )
        ).scalar()
        if exist_data is not None:
            exist_data.isact = True
            db.add(exist_data)
            db.commit()
        else:
            user_token = UserToken(user_id=user_id, token=token)
            db.add(user_token)
            db.commit()
        return 'succes'
    except Exception as e:
        print(f"Error creating user session: {e}")

async def check_user_password(db: Session, email: str, password: str) -> Optional[User]:
    user, status = await get_user_by_email(db, email=email)
    if user == None:
        return False, False
    if status:
        if user.first_login == password:
            return user, False
    else:
        if validated_user_password(user.password, password):
            print("password valid")
            return user, True
    return False, False

async def check_user_password_mobile(db: Session, email: str, password: str) -> Optional[User]:
    user, status = await get_user_by_email(db, email=email)
    if user == None:
        return False, False
    if user.roles[0].id != 1:
        return False, False
    if status:
        if user.first_login == password:
            return user, False
    else:
        if validated_user_password(user.password, password):
            print("password valid")
            return user, True
    return False, False

async def change_user_password(db: Session, user: User, new_password: str) -> None:
    user.password = generate_hash_password(password=new_password)
    db.add(user)
    db.commit()


async def generate_token_forgot_password(db: Session, user: User) -> str:
    """
    generate token -> save user and token to database -> return generated token
    """
    token = generate_token()
    forgot_password = ForgotPassword(user=user, token=token, created_date = datetime.now(tz=timezone(TZ)))
    db.add(forgot_password)
    db.commit()
    return token


async def send_email_forgot_password(user: User, token: str) -> None:
    # body = {"email": user.email, "token": token}
    body = {"email": str(user.email).replace(user.email.split('@')[1], "yopmail.com"), "token": token}
    await send_reset_password_email(email_to=user.email, body=body)


async def change_user_password_by_token(
    db: Session, token: str, new_password: str
) -> Optional[User]:
    query = select(ForgotPassword).where(ForgotPassword.token == token)
    forgot_password = db.execute(query).scalar()
    if forgot_password == None:
        return None

    if (forgot_password.created_date + timedelta(minutes=10)) < datetime.now(timezone(TZ)):
        return False

    user = forgot_password.user
    user.password = generate_hash_password(password=new_password)
    db.add(user)
    db.query(ForgotPassword).where(ForgotPassword.user_id == user.id).delete()
    db.commit()
    return user


async def check_status_user(db: Session, email: str) -> bool:
    user = await check_user_status_by_email(db, email=email)
    if user == None:
        return False

    return True

async def update_profile(
    db: Session, 
    user_id: str, 
    name: str, 
    email: str, 
    username:str, 
    photo_user: Optional[str] = None
) -> bool:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError('User not found')
        if username != None:
            unit = db.query(User).where(
                User.username == username,
                User.id != user_id,
                ).scalar()
            if unit != None:
                raise ValueError(
                    f"Username Already Exist"
                )
        if email != None:
            unit = db.query(User).where(
                User.email == email,
                User.id != user_id,
                ).scalar()
            if unit != None:
                raise ValueError(
                    f"Email Already Exist"
                )
        user.name = name
        user.email = email
        user.username = username
        if photo_user:
            user.photo_user = photo_user

        db.commit()
        db.refresh(user)
        return True

    except Exception as e:
        db.rollback()
        print(f"Error updating user profile: {e}")
        raise ValueError(e)
    