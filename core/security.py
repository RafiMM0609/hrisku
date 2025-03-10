from typing import List, Optional
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from pytz import timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from models.Permission import Permission
from models.User import User
# from models.Permission import Permission
from settings import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM, TZ

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def generate_hash_password(password: str) -> str:
    hash = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
    return hash.decode()

def generate_hash_lisensi(lisensi: str) -> str:
    hash = bcrypt.hashpw(str.encode(lisensi), bcrypt.gensalt())
    return hash.decode()


def validated_user_password(hash: str, password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hash.encode())
    except:
        return False


async def generate_jwt_token_from_user(
    user: User, ignore_timezone: bool = False
) -> str:
    # expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now() + timedelta(minutes=60*24)
    # expire = datetime.now() + timedelta(minutes=1)
    if ignore_timezone == False:  # For testing
        expire = expire.astimezone(timezone(TZ))
    """
    {
    "user_id": 671,
    "username": "bima@qti.co.id",
    "email": "bima@qti.co.id",
    "exp": 1641455971,
    }
    """
    payload = {
        "id": str(user.id),
        "username": user.email,
        "email": user.email,
        "exp": expire,
    }
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return jwt_token

async def generate_refresh_jwt_token_from_user(
    user: User, ignore_timezone: bool = False
) -> str:
    # expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now() + timedelta(minutes=60*15)
    # expire = datetime.now() + timedelta(minutes=1)
    if ignore_timezone == False:  # For testing
        expire = expire.astimezone(timezone(TZ))
    """
    {
    "user_id": 671,
    "username": "bima@qti.co.id",
    "email": "bima@qti.co.id",
    "exp": 1641455971,
    }
    """
    payload = {
        "id": str(user.id),
        "username": user.email,
        "email": user.email,
        "exp": expire,
    }
    jwt_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return jwt_token


def get_user_from_jwt_token(db: Session, jwt_token: str) -> Optional[User]:
    try:
        payload = jwt.decode(token=jwt_token, key=SECRET_KEY, algorithms=ALGORITHM)
        if payload["exp"] < datetime.now().timestamp():
            return None
        id = payload.get("id")
        query = select(User).where(User.id == id)
        user = db.execute(query).scalar()
    except JWTError:
        return None
    except Exception as e:
        return None
    return user


def get_user_permissions(db: Session, user: User) -> List[Permission]:
    permissions = []

    # add permission from role
    for role in user.roles:
        for permission in role.permissions:
            exists = [x for x in permissions if x == permission]
            if len(exists) == 0:
                permissions.append(permission)
    return sorted(permissions, key=lambda d: d.id)


def is_user_has_permission(
    db: Session, user: User, permission_name: str, module_name: Optional[str] = None
) -> bool:
    # stmt = (
    #     select(Permission)
    #     .join(Module, Permission.module)
    #     .where(Permission.permission == permission_name)
    #     .where(Module.nama == module_name)
    # )
    # permission: Optional[Permission] = db.execute(stmt).scalar()
    # if permission == None: # NOQA
    #     return False

    # stmt = select(UserPermission).where(
    #     UserPermission.user_id == user.id, UserPermission.permission_id == permission.id
    # )
    # user_permission: Optional[UserPermission] = db.execute(stmt).scalar()
    # if user_permission != None: # NOQA
    #     return user_permission.grant

    # is_permission_exists = False
    # stmt = select(Module).where(Module.nama == module_name)
    # module = db.execute(stmt).scalar()
    # for role in user.roles:
    #     permissions: List[Permission] = role.permissions
    #     for permission in permissions:
    #         if permission.permission == permission_name:
    #             if module != None: # NOQA
    #                 if permission.module_id == module.id:
    #                     is_permission_exists = True
    #             else:
    #                 if permission.module_id == None: # NOQA
    #                     is_permission_exists = True

    return False


def migrate_from_single_role_to_multiple_role(db: Session, is_commit: bool = True):
    stmt = select(User)
    all_user: List[User] = db.execute(stmt).scalars().all()
    for user in all_user:
        user.roles = [user.role]
        db.add(user)

    if is_commit == True:
        db.commit()
