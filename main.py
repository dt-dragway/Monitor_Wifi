from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from backend.database import create_db_and_tables
from backend.scheduler import start_all_background_tasks, stop_all_background_tasks

# Importamos los routers
from backend.routers.devices import router as devices_router
from backend.routers.security import router as security_router
from backend.routers.traffic import router as traffic_router
from backend.routers.system import router as system_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    start_all_background_tasks()
    yield
    stop_all_background_tasks()

app = FastAPI(title="Monitor Wifi Profesional", lifespan=lifespan)

# Montar archivos estáticos
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(BASE_DIR, "templates/index.html")) as f:
        return f.read()

# Registrar routers
app.include_router(devices_router)
app.include_router(security_router)
app.include_router(traffic_router)
app.include_router(system_router)
