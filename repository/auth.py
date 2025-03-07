from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import validated_user_password, generate_hash_password
from core.utils import generate_token
from core.mail import send_reset_password_email
from models.User import User
from models.ForgotPassword import ForgotPassword
from models.UserToken import UserToken
from datetime import datetime, timedelta
from pytz import timezone
from settings import TZ

async def check_user_status_by_email(
    db: AsyncSession,
    email: str
) -> Optional[User]:

    query = select(User).filter(
                func.lower(User.email) == email.lower(),
                User.is_active == True
            )

    user = db.execute(query).scalar()
    return user


async def get_user_by_email(
    db: AsyncSession, email: str, exclude_soft_delete: bool = True
) -> Optional[User]:
    try:
        if exclude_soft_delete == True:
            query = select(User).filter(func.lower(User.email) == email.lower(), User.deleted_at == None)
        else:
            # why there is delete_at and is_active
            query = select(User).filter(func.lower(User.email) == email.lower(), User.is_active == True)
        user = db.execute(query).scalar()
        return user
    except Exception as e:
        print(e)
        return None
async def get_user_by_username(
    db: AsyncSession, username: str, exclude_soft_delete: bool = True
) -> Optional[User]:
    try:
        if exclude_soft_delete == True:
            query = select(User).filter(func.lower(User.username) == username.lower(), User.deleted_at == None)
        else:
            # why there is delete_at and is_active
            query = select(User).filter(func.lower(User.username) == username.lower(), User.is_active == True)
        user = db.execute(query).scalar()
        return user
    except Exception as e:
        print(e)
        return None
    
async def delete_user_session(db: AsyncSession, user_id: str, token=str) -> str:
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
    
async def create_user_session(db: AsyncSession, user_id: str, token:str) -> str:
    try:
        exist_data = db.execute(
            select(UserToken).filter(
                UserToken.user_id == user_id,
                UserToken.token == token
            )
        ).scalar()
        if exist_data is not None:
            exist_data.is_active = True
            db.add(exist_data)
            db.commit()
        else:
            user_token = UserToken(user_id=user_id, token=token)
            db.add(user_token)
            db.commit()
        return 'succes'
    except Exception as e:
        print(f"Error creating user session: {e}")
async def create_user_session_me(db: AsyncSession, user_id: str, token:str, old_token:str) -> str:
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
                UserToken.user_id == user_id,
                UserToken.token == token
            )
        ).scalar()
        if exist_data is not None:
            exist_data.is_active = True
            db.add(exist_data)
            db.commit()
        else:
            user_token = UserToken(user_id=user_id, token=token)
            db.add(user_token)
            db.commit()
        return 'succes'
    except Exception as e:
        print(f"Error creating user session: {e}")

async def check_user_password(db: AsyncSession, email: str, password: str) -> Optional[User]:
    user = await get_user_by_email(db, email=email)
    if user == None:
        return False
    if validated_user_password(user.password, password):
        return user
    return False

async def change_user_password(db: AsyncSession, user: User, new_password: str) -> None:
    user.password = generate_hash_password(password=new_password)
    db.add(user)
    db.commit()


async def generate_token_forgot_password(db: AsyncSession, user: User) -> str:
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
    db: AsyncSession, token: str, new_password: str
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


async def check_status_user(db: AsyncSession, email: str) -> bool:
    user = await check_user_status_by_email(db, email=email)
    if user == None:
        return False

    return True

async def update_profile(
    db: AsyncSession, 
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
    