
from fastapi import FastAPI, Request
# import logging
import time
# import uvicorn
from settings import (
    ENVIRONTMENT,
    SENTRY_DSN,
    SENTRY_TRACES_SAMPLE_RATES,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
import sentry_sdk

from routes.auth import router as AuthRouter
from routes.user_management import router as UserRouter
from routes.role import router as RoleRouter
from routes.client import router as ClientRouter
from routes.clientbilling import router as ClientBillingRouter
from routes.file import router as FileRouter
from routes.talent_mapping import router as TalentMappingRouter
from routes.talent_monitor import router as TalentMonitorRouter
from routes.mobile import router as MobileRouter
from routes.outlet import router as OutletRouter
from routes.nationalholiday import router as NationalHolidayRouter
from routes.permission import router as PermissionRouter
from routes.historypayment import router as HistoryPaymentRouter

if SENTRY_DSN != None:  # NOQA
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATES,
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
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
# app.add_middleware(HTTPSRedirectMiddleware) # Untuk batasi hanya https
# app.add_middleware(GZipMiddleware, minimum_size=500)  # Hanya mengompresi response di atas 500 byte

app.include_router(AuthRouter, prefix="/auth")
app.include_router(UserRouter, prefix="/user")
app.include_router(RoleRouter, prefix="/role")
app.include_router(ClientRouter, prefix="/client")
app.include_router(ClientBillingRouter, prefix="/client-billing")
app.include_router(TalentMappingRouter, prefix="/talent-mapping")
app.include_router(TalentMonitorRouter, prefix="/talent-monitor")
app.include_router(FileRouter, prefix="/file")
app.include_router(OutletRouter, prefix="/outlet")
app.include_router(MobileRouter, prefix="/mobile")
app.include_router(NationalHolidayRouter, prefix="/holiday")
app.include_router(PermissionRouter, prefix="/permission")
app.include_router(HistoryPaymentRouter, prefix="/history-payment")

@app.get("/")
async def read_root():  # <-- Perbaikan di sini
    try:
        return {"message": "Hello welcome to hrisku"}
    except Exception as e:
        return {"error": str(e)}


# logging.basicConfig(level=logging.INFO)

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     start_time = time.time()
#     logging.info(f"Request: {request.method} {request.url}")
#     response = await call_next(request)
#     duration = time.time() - start_time
#     logging.info(f"Response: {response.status_code} in {duration:.2f} seconds")
#     return response
# @app.on_event("startup")
# async def startup_event():
#     app.state.db_client = await get_db()

# @app.on_event("shutdown")
# async def shutdown_event():
#     await app.state.db_client.close()

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


