from fastapi import FastAPI, Response

from app.api.log_ingestion import router as log_ingestion_router
from app.api.change_detection import router as change_detection_router
from app.api.tenant_config import router as tenant_config_router
from app.db.database import init_db

app = FastAPI()


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"message": "Magellan backend is running"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


app.include_router(
    log_ingestion_router,
    prefix="/logs"
)

app.include_router(
    change_detection_router,
    prefix="/snapshots"
)

app.include_router(
    tenant_config_router,
    prefix="/config"
)

