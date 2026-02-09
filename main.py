from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
import threading
import time
import asyncio
from typing import List

from backend.database import create_db_and_tables, get_session, engine
from backend.models import Device
from backend.service import update_network_status

# Variable global para controlar el hilo
scanning_active = True

def background_scanner():
    """Hilo que ejecuta el escaneo periódicamente"""
    while scanning_active:
        try:
            update_network_status()
        except Exception as e:
            print(f"Error en escaneo: {e}")
        time.sleep(30) # Escanear cada 30 segundos

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Iniciar hilo de escaneo
    t = threading.Thread(target=background_scanner, daemon=True)
    t.start()
    yield
    # Clean up if needed (e.g., stop thread)
    global scanning_active
    scanning_active = False

# Crear aplicación FastAPI
app = FastAPI(title="Monitor Wifi Profesional", lifespan=lifespan)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="/media/Jesus-Aroldo/Anexo/Desarrollos  /Monitor_Wifi/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("/media/Jesus-Aroldo/Anexo/Desarrollos  /Monitor_Wifi/templates/index.html") as f:
        return f.read()

@app.get("/api/devices", response_model=List[Device])
def get_devices(session: Session = Depends(get_session)):
    devices = session.exec(select(Device)).all()
    return devices

@app.post("/api/devices/{mac}/trust")
def trust_device(mac: str, is_trusted: bool, session: Session = Depends(get_session)):
    device = session.get(Device, mac)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_trusted = is_trusted
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

@app.post("/api/devices/{mac}/alias")
def set_alias(mac: str, alias: str, session: Session = Depends(get_session)):
    device = session.get(Device, mac)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.alias = alias
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_network_status)
    return {"message": "Escaneo iniciado manualmente"}
