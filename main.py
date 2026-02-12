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
from backend.models import Device, EventLog, Settings, SpeedTestResult, IntruderLog
from backend.service import update_network_status
from backend.nmap_scanner import scan_device_details, scan_vulnerabilities
from backend.mitm_detector import mitm_detector
from backend.blocker import blocker
from backend.jail import jailer
from backend.traffic_analyzer import start_sniffer_thread, get_traffic_stats
from backend.speedtest_monitor import run_speedtest
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
    
    # Iniciar módulos de seguridad
    blocker.start()
    jailer.start()
    start_sniffer_thread() # Traffic Analyzer (Phase 21)

    # SCHEDULER: Speedtest cada 4 horas
    def speedtest_scheduler():
        while scanning_active:
            time.sleep(14400) # 4 horas
            try:
                run_speedtest()
            except Exception as e:
                print(f"Error scheduled speedtest: {e}")

    t_st = threading.Thread(target=speedtest_scheduler, daemon=True)
    t_st.start()

    # RESTAURAR ESTADO DE BLOQUEO (Persistencia)
    print("♻️ Restaurando reglas de bloqueo desde base de datos...")
    with Session(engine) as session:
        blocked_devices = session.exec(select(Device).where(Device.is_blocked == True)).all()
        for device in blocked_devices:
            print(f"🔒 Bloqueando persistente: {device.ip} ({device.mac})")
            # 1. Jail (Wall of Shame + DNS Trap)
            if device.ip:
                 jailer.add_prisoner(device.ip, device.mac)
            # 2. Deauth (Active Blocking)
            blocker.block_device(device.mac)

    yield
    # Clean up if needed (e.g., stop thread)
    global scanning_active
    scanning_active = False

# Crear aplicación FastAPI
app = FastAPI(title="Monitor Wifi Profesional", lifespan=lifespan)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="/media/Jesus-Aroldo/Anexo/Desarrollos  /Monitor_Wifi/static"), name="static")

@app.post("/api/devices/{ip}/warn")
def warn_device(ip: str, session: Session = Depends(get_session)):
    # Find MAC (needed for better Arp Spoofing & Blocking)
    statement = select(Device).where(Device.ip == ip)
    device = session.exec(statement).first()
    
    mac = device.mac if device else None
    
    # 1. Apply Logic (Jail + Block)
    jailer.add_prisoner(ip, mac)
    
    if device:
        blocker.block_device(device.mac)
        # PERSISTENCE: Save to DB
        device.is_blocked = True
        session.add(device)
        session.commit()
        
    return {"success": True, "status": "jailed", "ip": ip}

@app.post("/api/devices/{ip}/unwarn")
def unwarn_device(ip: str, session: Session = Depends(get_session)):
    # 1. Release Logic
    jailer.release_prisoner(ip)
    
    # Find MAC to unblock too
    statement = select(Device).where(Device.ip == ip)
    device = session.exec(statement).first()
    
    if device:
        blocker.unblock_device(device.mac)
        # PERSISTENCE: Save to DB
        device.is_blocked = False
        session.add(device)
        session.commit()

    return {"success": True, "status": "released", "ip": ip}

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
def warn_device(ip: str, session: Session = Depends(get_session)):
    # 1. Apply Logic (Jail + Block)
    jailer.add_prisoner(ip)
    
    # Find MAC to block too (Unified)
    # We need the device from DB to know MAC
    statement = select(Device).where(Device.ip == ip)
    device = session.exec(statement).first()
    
    mac = None
    if device:
        mac = device.mac
        blocker.block_device(device.mac)
        # PERSISTENCE: Save to DB
        device.is_blocked = True
        session.add(device)
        session.commit()
    
    from backend.logger import log_event
    log_event("DANGER", f"Protocolo de Expulsión ACTIVADO para {ip}", mac)
        
    return {"success": True, "status": "jailed", "ip": ip}

@app.post("/api/devices/{ip}/unwarn")
def unwarn_device(ip: str, session: Session = Depends(get_session)):
    # 1. Release Logic
    jailer.release_prisoner(ip)
    
    # Find MAC to unblock too
    statement = select(Device).where(Device.ip == ip)
    device = session.exec(statement).first()
    
    mac = None
    if device:
        mac = device.mac
        blocker.unblock_device(device.mac)
        # PERSISTENCE: Save to DB
        device.is_blocked = False
        session.add(device)
        session.commit()

    from backend.logger import log_event
    log_event("INFO", f"Protocolo de Expulsión DESACTIVADO para {ip}", mac)

    return {"success": True, "status": "released", "ip": ip}

@app.get("/api/jailed_devices")
def get_jailed_devices():
    return {"jailed": list(jailer.victims)}

@app.get("/api/backup")
def export_backup(session: Session = Depends(get_session)):
    devices = session.exec(select(Device)).all()
    return {"devices": devices}

@app.post("/api/backup")
def import_backup(data: dict, session: Session = Depends(get_session)):
    try:
        devices_data = data.get("devices", [])
        count = 0
        for d in devices_data:
            mac = d.get('mac')
            if not mac: continue
            
            # Upsert
            existing = session.get(Device, mac)
            if existing:
                # Update critical fields
                if d.get('alias'): existing.alias = d.get('alias')
                if d.get('is_trusted') is not None: existing.is_trusted = d.get('is_trusted')
                if d.get('is_blocked') is not None: existing.is_blocked = d.get('is_blocked')
                
                session.add(existing)
            else:
                # Create new (offline)
                valid_keys = Device.__fields__.keys()
                filtered_d = {k: v for k, v in d.items() if k in valid_keys}
                
                new_d = Device(**filtered_d)
                new_d.status = "offline" 
                session.add(new_d)
            count += 1
        
        session.commit()
        from backend.logger import log_event
        log_event("SYSTEM", f"Restauración de Backup completada ({count} dispositivos).")
        return {"success": True, "count": count}
    except Exception as e:
        print(f"Error importando backup: {e}")
        return {"success": False, "error": str(e)}

from backend.models import Device, EventLog, Settings, TrafficLog
from datetime import datetime, timedelta

@app.get("/api/traffic/history/{mac}")
def get_traffic_history(mac: str, period: str = "24h", session: Session = Depends(get_session)):
    query = select(TrafficLog).where(TrafficLog.device_mac == mac).order_by(TrafficLog.timestamp.asc())
    
    now = datetime.utcnow()
    cutoff = None
    
    if period == "24h": cutoff = now - timedelta(hours=24)
    if period == "7d": cutoff = now - timedelta(days=7)
    if period == "30d": cutoff = now - timedelta(days=30)
    if period == "365d": cutoff = now - timedelta(days=365)
    # period == "all" implies no cutoff
    
    if cutoff:
        query = query.where(TrafficLog.timestamp >= cutoff)
        
    logs = session.exec(query).all()
    return logs

@app.get("/api/events")
def get_events(limit: int = 7, session: Session = Depends(get_session)):
    """
    Retorna los eventos recientes (log de actividad).
    Por defecto muestra las últimas 7 notificaciones.
    """
    events = session.exec(select(EventLog).order_by(EventLog.timestamp.desc()).limit(limit)).all()
    return events

@app.get("/api/traffic/monthly")
def get_monthly_traffic(session: Session = Depends(get_session)):
    """
    Returns total traffic per device for the current month.
    Used for Top Talkers chart.
    """
    now = datetime.utcnow()
    # First day of month
    start_of_month = datetime(now.year, now.month, 1)
    
    # Query all logs since start of month
    # Efficient aggregation would be better in SQL, but SQLModel/SQLite support varies.
    # We'll fetch and sum in Python for simplicity and compatibility.
    query = select(TrafficLog).where(TrafficLog.timestamp >= start_of_month)
    logs = session.exec(query).all()
    
    # Aggregate
    stats = {}
    for log in logs:
        if log.device_mac not in stats:
            stats[log.device_mac] = {'down': 0, 'up': 0}
        stats[log.device_mac]['down'] += log.bytes_down
        stats[log.device_mac]['up'] += log.bytes_up
        
    return stats

@app.get("/api/settings/webhook")
def get_webhook(session: Session = Depends(get_session)):
    setting = session.get(Settings, "webhook_url")
    return {"url": setting.value if setting else ""}

@app.post("/api/settings/webhook")
def set_webhook(data: dict, session: Session = Depends(get_session)):
    url = data.get("url", "")
    setting = session.get(Settings, "webhook_url")
    if not setting:
        setting = Settings(key="webhook_url", value=url)
    else:
        setting.value = url
    session.add(setting)
    session.commit()
    
    # Test notification
    if url:
        from backend.notifier import send_notification
        send_notification("Webhook configurado correctamente.", "INFO")
        
    
    return {"success": True}

@app.get("/api/speedtest/history")
def get_speedtest_history(limit: int = 10, session: Session = Depends(get_session)):
    results = session.exec(select(SpeedTestResult).order_by(SpeedTestResult.timestamp.desc()).limit(limit)).all()
    return results

@app.post("/api/speedtest/run")
async def trigger_speedtest():
    loop = asyncio.get_event_loop()
    # Ejecutar en hilo para no bloquear
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, run_speedtest)
    
    if result:
        return {"success": True, "data": result}
    return {"success": False, "error": "Failed to run speedtest"}

@app.get("/api/traffic")
def read_traffic_stats():
    return get_traffic_stats()

@app.get("/api/topology")
def get_topology(session: Session = Depends(get_session)):
    devices = session.exec(select(Device).where(Device.status == "online")).all()
    
    nodes = []
    edges = []
    
    # Gateway Node
    nodes.append({"id": "gateway", "label": "Gateway\n(Internet)", "group": "gateway", "value": 10})
    
    # Monitor Node
    nodes.append({"id": "monitor", "label": "Monitor Pro", "group": "server", "value": 8})
    edges.append({"from": "monitor", "to": "gateway"})
    
    for d in devices:
        group = "device"
        val = 5
        if d.is_blocked: 
            group = "blocked"
            val = 3
        elif not d.is_trusted: 
            group = "intruder"
            val = 6
        elif d.is_trusted: 
            group = "trusted"

        label = d.alias or d.vendor or d.ip
        nodes.append({
            "id": d.mac,
            "label": f"{label}\n({d.ip})",
            "group": group,
            "value": val,
            "title": f"MAC: {d.mac}\nVendor: {d.vendor}"
        })
        edges.append({"from": d.mac, "to": "gateway"})
        
    return {"nodes": nodes, "edges": edges}

@app.get("/api/intruders")
def get_intruders(limit: int = 50, session: Session = Depends(get_session)):
    """
    Retorna el registro de intrusos detectados.
    Por defecto muestra los últimos 50 registros.
    """
    intruders = session.exec(
        select(IntruderLog)
        .order_by(IntruderLog.timestamp.desc())
        .limit(limit)
    ).all()
    return intruders

# --- CONFIGURACIÓN DE RED ---
# (Endpoints de subnets están definidos más abajo junto con el modelo Pydantic)

# --- ADMIN RESET ---
from sqlmodel import delete

@app.post("/api/admin/reset_db")
def reset_db_endpoint(session: Session = Depends(get_session)):
    """
    Borra todos los datos de dispositivos, logs y tráfico.
    Mantiene la configuración.
    """
    try:
        # Borrar tablas de datos
        session.exec(delete(Device))
        session.exec(delete(EventLog))
        session.exec(delete(TrafficLog))
        session.exec(delete(IntruderLog))
        session.exec(delete(SpeedTestResult))
        # No borrar Settings
        
        session.commit()
        
        # Limpiar memoria del analizador
        try:
            from backend.traffic_analyzer import known_macs, traffic_stats
            known_macs.clear()
            traffic_stats.clear()
        except: pass
            
        print("☢️ Base de datos reiniciada por el usuario.")
        return {"status": "success", "message": "Base de datos limpia"}
        
    except Exception as e:
        print(f"Error reset DB: {e}")
        # Fallback a método SQLAlchemy si delete falla
        try:
            session.query(Device).delete()
            session.query(EventLog).delete()
            session.query(TrafficLog).delete()
            session.query(IntruderLog).delete()
            session.query(SpeedTestResult).delete()
            session.commit()
            return {"status": "success", "message": "Base de datos limpia (Legacy)"}
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Error borrando DB: {e} | {e2}")

from pydantic import BaseModel

class SubnetsConfig(BaseModel):
    subnets: str

@app.get("/api/config/subnets")
def get_scan_subnets(session: Session = Depends(get_session)):
    """Obtiene la lista de subredes configuradas para escanear"""
    setting = session.get(Settings, "scan_subnets")
    return {"subnets": setting.value if setting else ""}

@app.post("/api/config/subnets")
def set_scan_subnets(config: SubnetsConfig, session: Session = Depends(get_session)):
    """Guarda la lista de subredes para escanear (separadas por coma)"""
    setting = session.get(Settings, "scan_subnets")
    if not setting:
        setting = Settings(key="scan_subnets", value=config.subnets)
    else:
        setting.value = config.subnets
    
    session.add(setting)
    session.commit()
    session.refresh(setting)
    
    # Trigger inmediato de escaneo en background
    # Opcional, pero útil para feedback rápido
    return {"status": "updated", "subnets": setting.value}
