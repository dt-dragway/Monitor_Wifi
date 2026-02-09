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
from backend.nmap_scanner import scan_device_details, scan_vulnerabilities
from backend.mitm_detector import mitm_detector
from backend.blocker import blocker
from backend.jail import jailer
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
    
    # Iniciar módulo de bloqueo
    blocker.start()
    
    # Iniciar módulo Jail (Wall of Shame)
    jailer.start()

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

@app.post("/api/scan/{ip}/deep")
async def deep_scan(ip: str):
    """
    Ejecuta un escaneo profundo (Nmap) sobre una IP específica.
    """
    loop = asyncio.get_event_loop()
    # Ejecutar en un hilo separado para no bloquear
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, scan_device_details, ip)
    
    if "error" in result:
        # Si falla (ej: nmap no instalado), devolvemos el error pero como 200/JSON para manejarlo en front
        return {"success": False, "error": result["error"]}
        
    return {"success": True, "data": result}

@app.post("/api/scan/{ip}/audit")
async def audit_device(ip: str):
    """
    Ejecuta una auditoría de seguridad (vulnerabilidades) sobre una IP.
    """
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, scan_vulnerabilities, ip)
        
    return result

@app.get("/api/security/status")
def get_security_status():
    """
    Retorna el estado de seguridad de la red (MITM check).
    """
    # Ejecutar chequeo (puede ser ligero, no bloqueante si usa cache de tiempo)
    return mitm_detector.check_security()

@app.post("/api/devices/{mac}/block")
def block_device(mac: str):
    blocker.block_device(mac)
    return {"success": True, "status": "blocked", "mac": mac}

@app.post("/api/devices/{mac}/unblock")
def unblock_device(mac: str):
    blocker.unblock_device(mac)
    return {"success": True, "status": "unblocked", "mac": mac}

@app.get("/api/blocked_devices")
def get_blocked_devices():
    return {"blocked": blocker.get_blocked_list()}

@app.post("/api/devices/{ip}/warn")
def warn_device(ip: str):
    jailer.add_prisoner(ip)
    return {"success": True, "status": "jailed", "ip": ip}

@app.post("/api/devices/{ip}/unwarn")
def unwarn_device(ip: str):
    jailer.release_prisoner(ip)
    return {"success": True, "status": "released", "ip": ip}

@app.get("/api/jailed_devices")
def get_jailed_devices():
    return {"jailed": list(jailer.victims)}
