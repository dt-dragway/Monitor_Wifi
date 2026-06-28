from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from backend.database import get_session
from backend.models import Device
from backend.blocker import blocker
from backend.jail import jailer
from backend.logger import log_event

router = APIRouter(prefix="/api/devices", tags=["devices"])

@router.get("", response_model=List[Device])
def get_devices(session: Session = Depends(get_session)):
    devices = session.exec(select(Device)).all()
    return devices

@router.post("/{mac}/trust")
def trust_device(mac: str, is_trusted: bool, session: Session = Depends(get_session)):
    device = session.get(Device, mac)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.is_trusted = is_trusted
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

@router.post("/{mac}/alias")
def set_alias(mac: str, alias: str, session: Session = Depends(get_session)):
    device = session.get(Device, mac)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.alias = alias
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

@router.post("/{mac}/block")
def block_device(mac: str):
    blocker.block_device(mac)
    return {"success": True, "status": "blocked", "mac": mac}

@router.post("/{mac}/unblock")
def unblock_device(mac: str):
    blocker.unblock_device(mac)
    return {"success": True, "status": "unblocked", "mac": mac}

@router.post("/{ip}/warn")
def warn_device(ip: str, session: Session = Depends(get_session)):
    statement = select(Device).where(Device.ip == ip)
    device = session.exec(statement).first()
    
    mac = device.mac if device else None
    
    if mac:
        jailer.add_prisoner(ip, mac)
        blocker.block_device(mac)
        device.is_blocked = True
        session.add(device)
        session.commit()
    else:
        # Fallback if device not found by ip
        jailer.add_prisoner(ip)
    
    log_event("DANGER", f"Protocolo de Expulsión ACTIVADO para {ip}", mac)
    return {"success": True, "status": "jailed", "ip": ip}

@router.post("/{ip}/unwarn")
def unwarn_device(ip: str, session: Session = Depends(get_session)):
    jailer.release_prisoner(ip)
    
    statement = select(Device).where(Device.ip == ip)
    device = session.exec(statement).first()
    
    mac = None
    if device:
        mac = device.mac
        blocker.unblock_device(mac)
        device.is_blocked = False
        session.add(device)
        session.commit()

    log_event("INFO", f"Protocolo de Expulsión DESACTIVADO para {ip}", mac)
    return {"success": True, "status": "released", "ip": ip}
