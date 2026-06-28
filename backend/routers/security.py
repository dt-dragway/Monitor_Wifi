from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session, select
import os
from datetime import datetime

from backend.database import get_session
from backend.models import IntruderLog, Vulnerability, Credential
from backend.blocker import blocker
from backend.jail import jailer
from backend.mitm_detector import mitm_detector
from backend.dns_spoofer import dns_spoofer
from backend.jail import get_local_ip, get_default_iface_name
from backend.scanner import get_network_interfaces

router = APIRouter(prefix="/api/security", tags=["security"])

@router.get("/status")
def get_security_status():
    return mitm_detector.check_security()

@router.get("/vulnerabilities")
def get_vulnerabilities(limit: int = 50, session: Session = Depends(get_session)):
    vulns = session.exec(
        select(Vulnerability).order_by(Vulnerability.timestamp.desc()).limit(limit)
    ).all()
    return vulns

@router.get("/vulnerabilities/{mac}")
def get_device_vulnerabilities(mac: str, session: Session = Depends(get_session)):
    vulns = session.exec(select(Vulnerability).where(Vulnerability.device_mac == mac)).all()
    return vulns

@router.get("/audit_summary")
def get_audit_summary(session: Session = Depends(get_session)):
    vulns = session.exec(select(Vulnerability)).all()
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for v in vulns:
        severity_counts[v.severity] = severity_counts.get(v.severity, 0) + 1
        
    return {
        "total_vulnerabilities": len(vulns),
        "severity_breakdown": severity_counts,
        "mitm_status": mitm_detector.check_security()["status"],
        "honeypot_active": True
    }

@router.get("/captures")
def list_captures():
    path = "security_audits/captures"
    if not os.path.exists(path):
        return []
    
    files = []
    for f in os.listdir(path):
        if f.endswith(".pcap"):
            full_path = os.path.join(path, f)
            stats = os.stat(full_path)
            files.append({
                "name": f,
                "size": stats.st_size,
                "date": datetime.fromtimestamp(stats.st_mtime).isoformat()
            })
    files.sort(key=lambda x: x['date'], reverse=True)
    return files

@router.get("/captures/download/{filename}")
def download_capture(filename: str):
    safe_name = os.path.basename(filename)
    file_path = os.path.join("security_audits/captures", safe_name)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=safe_name,
            media_type='application/vnd.tcpdump.pcap'
        )
    return {"error": "Archivo no encontrado"}

@router.post("/rogue_ap/start")
async def start_rogue_ap(ssid: str = "FREE_WIFI_PUBLIC", interface: str = "wlan1"):
    try:
        from backend.rogue_ap import rogue_ap_manager
        success = rogue_ap_manager.start(ssid, interface)
        return {"success": success, "message": "Evil Twin iniciado" if success else "Error al iniciar"}
    except Exception as e:
        return {"error": str(e)}

@router.post("/rogue_ap/stop")
async def stop_rogue_ap():
    try:
        from backend.rogue_ap import rogue_ap_manager
        rogue_ap_manager.stop()
        return {"success": True}
    except Exception as e:
        return {"error": str(e)}

@router.get("/rogue_ap/status")
def get_rogue_ap_status():
    try:
        from backend.rogue_ap import rogue_ap_manager
        return rogue_ap_manager.get_status()
    except:
        return {"active": False}

@router.get("/credentials")
def get_credentials(limit: int = 50, session: Session = Depends(get_session)):
    creds = session.exec(
        select(Credential).order_by(Credential.timestamp.desc()).limit(limit)
    ).all()
    return creds

@router.post("/dns_spoof/start")
async def start_dns_spoof(domain: str, target: str, interface: str = None):
    iface = interface or get_default_iface_name()
    dns_spoofer.start(iface, {domain: target})
    return {"success": True, "message": f"Spoofing activo para {domain}"}

@router.post("/dns_spoof/stop")
async def stop_dns_spoof():
    dns_spoofer.stop()
    return {"success": True}

@router.get("/dns_spoof/status")
def get_dns_spoof_status():
    return {
        "active": dns_spoofer.running,
        "rules": dns_spoofer.spoof_map
    }

@router.get("/attack_info")
def get_attack_info():
    iface = get_default_iface_name()
    return {
        "local_ip": get_local_ip(iface),
        "default_interface": iface,
        "all_interfaces": get_network_interfaces()
    }

# Endpoints que estaban en /api/ pero conceptualmente son de seguridad
@router.get("/blocked_devices", tags=["devices"])
def get_blocked_devices():
    return {"blocked": blocker.get_blocked_list()}

@router.get("/jailed_devices", tags=["devices"])
def get_jailed_devices():
    return {"jailed": list(jailer.victims)}

@router.get("/intruders")
def get_intruders(limit: int = 50, session: Session = Depends(get_session)):
    intruders = session.exec(
        select(IntruderLog).order_by(IntruderLog.timestamp.desc()).limit(limit)
    ).all()
    return intruders

@router.post("/scan_subnet")
async def global_subnet_scan(cidr: str = None):
    from backend.nmap_scanner import scan_subnet_fast
    target_cidr = cidr
    if not target_cidr:
        ifaces = get_network_interfaces()
        if ifaces:
            target_cidr = ifaces[0]['cidr']
        else:
            return {"error": "No se detectó una subred activa"}

    results = scan_subnet_fast(target_cidr)
    return results
