from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models.User import User
from models import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from settings import (
    ENVIRONTMENT
)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield
tittle="HRISKU"
if ENVIRONTMENT == 'dev':
    app = FastAPI(
        title=tittle,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
        # lifespan=lifespan,
        swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_ui_init_oauth={
            "clientId": "your-client-id",
            "authorizationUrl": "/auth/token",
            "tokenUrl": "/auth/token",
        },
    )
elif ENVIRONTMENT == 'prod':
        app = FastAPI(
        title=tittle,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        # lifespan=lifespan,
        swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_ui_init_oauth={
            "clientId": "your-client-id",
            "authorizationUrl": "/auth/token",
            "tokenUrl": "/auth/token",
        },
    )
app.add_middleware(
    CORSMiddleware,
    # allow_origins=CORS_ALLOWED_ORIGINS,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def read_root(db: AsyncSession = Depends(get_db)):  # <-- Perbaikan di sini
    try:
        return {"message": "Hello welcome to hrisku"}
    except Exception as e:
        await db.rollback()  # <-- Hindari data corrupt jika error terjadi
        return {"error": str(e)}
@app.post("/user")
async def read_root(db: AsyncSession = Depends(get_db)):  # <-- Perbaikan di sini
    try:
        new_user = User(
            email="user3@example.com",
            name="John Doe 3",
            phone="+628123456783",
            password="hashedpassword123"
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)  # <-- Pastikan data tersimpan sebelum digunakan
        return {"message": "User added!", "user_id": new_user.id}
    except Exception as e:
        await db.rollback()  # <-- Hindari data corrupt jika error terjadi
        return {"error": str(e)}