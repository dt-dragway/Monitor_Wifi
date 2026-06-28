from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select, delete
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel

from backend.database import get_session
from backend.models import Device, EventLog, TrafficLog, IntruderLog, SpeedTestResult, Settings
from backend.service import update_network_status
from backend.nmap_scanner import scan_device_details, scan_vulnerabilities
from backend.logger import log_event
from backend.notifier import send_notification

router = APIRouter(prefix="/api", tags=["system", "admin", "config"])

@router.post("/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_network_status)
    return {"message": "Escaneo iniciado manualmente"}

@router.post("/scan/{ip}/deep")
async def deep_scan(ip: str):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, scan_device_details, ip)
    
    if "error" in result:
        return {"success": False, "error": result["error"]}
        
    return {"success": True, "data": result}

@router.post("/scan/{ip}/audit")
async def audit_device(ip: str):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, scan_vulnerabilities, ip)
    return result

@router.get("/backup")
def export_backup(session: Session = Depends(get_session)):
    devices = session.exec(select(Device)).all()
    return {"devices": devices}

@router.post("/backup")
def import_backup(data: dict, session: Session = Depends(get_session)):
    try:
        devices_data = data.get("devices", [])
        count = 0
        for d in devices_data:
            mac = d.get('mac')
            if not mac: continue
            
            existing = session.get(Device, mac)
            if existing:
                if d.get('alias'): existing.alias = d.get('alias')
                if d.get('is_trusted') is not None: existing.is_trusted = d.get('is_trusted')
                if d.get('is_blocked') is not None: existing.is_blocked = d.get('is_blocked')
                session.add(existing)
            else:
                valid_keys = Device.__fields__.keys()
                filtered_d = {k: v for k, v in d.items() if k in valid_keys}
                new_d = Device(**filtered_d)
                new_d.status = "offline" 
                session.add(new_d)
            count += 1
        
        session.commit()
        log_event("SYSTEM", f"Restauración de Backup completada ({count} dispositivos).")
        return {"success": True, "count": count}
    except Exception as e:
        print(f"Error importando backup: {e}")
        return {"success": False, "error": str(e)}

@router.get("/events")
def get_events(limit: int = 7, session: Session = Depends(get_session)):
    events = session.exec(select(EventLog).order_by(EventLog.timestamp.desc()).limit(limit)).all()
    return events

@router.get("/settings/webhook")
def get_webhook(session: Session = Depends(get_session)):
    setting = session.get(Settings, "webhook_url")
    return {"url": setting.value if setting else ""}

@router.post("/settings/webhook")
def set_webhook(data: dict, session: Session = Depends(get_session)):
    url = data.get("url", "")
    setting = session.get(Settings, "webhook_url")
    if not setting:
        setting = Settings(key="webhook_url", value=url)
    else:
        setting.value = url
    session.add(setting)
    session.commit()
    
    if url:
        send_notification("Webhook configurado correctamente.", "INFO")
        
    return {"success": True}

@router.post("/admin/reset_db")
def reset_db_endpoint(session: Session = Depends(get_session)):
    try:
        session.exec(delete(Device))
        session.exec(delete(EventLog))
        session.exec(delete(TrafficLog))
        session.exec(delete(IntruderLog))
        session.exec(delete(SpeedTestResult))
        
        session.commit()
        
        try:
            from backend.traffic_analyzer import known_macs, traffic_stats
            known_macs.clear()
            traffic_stats.clear()
        except: pass
            
        print("☢️ Base de datos reiniciada por el usuario.")
        return {"status": "success", "message": "Base de datos limpia"}
        
    except Exception as e:
        print(f"Error reset DB: {e}")
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

class SubnetsConfig(BaseModel):
    subnets: str

@router.get("/config/subnets")
def get_scan_subnets(session: Session = Depends(get_session)):
    setting = session.get(Settings, "scan_subnets")
    return {"subnets": setting.value if setting else ""}

@router.post("/config/subnets")
def set_scan_subnets(config: SubnetsConfig, session: Session = Depends(get_session)):
    setting = session.get(Settings, "scan_subnets")
    if not setting:
        setting = Settings(key="scan_subnets", value=config.subnets)
    else:
        setting.value = config.subnets
    
    session.add(setting)
    session.commit()
    session.refresh(setting)
    
    return {"status": "updated", "subnets": setting.value}
