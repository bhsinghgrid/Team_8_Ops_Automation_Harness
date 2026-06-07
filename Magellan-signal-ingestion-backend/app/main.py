from fastapi import FastAPI, Response

from app.api.observations import router as observation_router
from app.api.signals import router as signal_router
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
    observation_router,
    prefix="/observations"
)

app.include_router(
    signal_router,
    prefix="/signals"
)
