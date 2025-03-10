from fastapi import FastAPI, Depends
# from app import app
# import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from settings import (
    ENVIRONTMENT
)

from routes.auth import router as AuthRouter
from routes.user_management import router as UserRouter
from routes.role import router as RoleRouter
from routes.file import router as FileRouter

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

app.include_router(AuthRouter, prefix="/auth")
app.include_router(UserRouter, prefix="/user")
app.include_router(RoleRouter, prefix="/role")
app.include_router(FileRouter, prefix="/file")

@app.get("/")
async def read_root():  # <-- Perbaikan di sini
    try:
        return {"message": "Hello welcome to hrisku"}
    except Exception as e:
        return {"error": str(e)}

# @app.on_event("startup")
# async def startup_event():
#     app.state.db_client = await get_db()

# @app.on_event("shutdown")
# async def shutdown_event():
#     await app.state.db_client.close()

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


