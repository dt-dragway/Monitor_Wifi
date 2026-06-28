from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.database import get_session
from backend.models import TrafficLog, SpeedTestResult, Device
from backend.traffic_analyzer import get_traffic_stats
from backend.speedtest_monitor import run_speedtest

router = APIRouter(prefix="/api", tags=["traffic", "speedtest", "topology"])

@router.get("/traffic")
def read_traffic_stats():
    return get_traffic_stats()

@router.get("/traffic/history/{mac}")
def get_traffic_history(mac: str, period: str = "24h", session: Session = Depends(get_session)):
    query = select(TrafficLog).where(TrafficLog.device_mac == mac).order_by(TrafficLog.timestamp.asc())
    
    now = datetime.utcnow()
    cutoff = None
    
    if period == "24h": cutoff = now - timedelta(hours=24)
    elif period == "7d": cutoff = now - timedelta(days=7)
    elif period == "30d": cutoff = now - timedelta(days=30)
    elif period == "365d": cutoff = now - timedelta(days=365)
    
    if cutoff:
        query = query.where(TrafficLog.timestamp >= cutoff)
        
    logs = session.exec(query).all()
    return logs

@router.get("/traffic/monthly")
def get_monthly_traffic(session: Session = Depends(get_session)):
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    query = select(TrafficLog).where(TrafficLog.timestamp >= start_of_month)
    logs = session.exec(query).all()
    
    stats = {}
    for log in logs:
        if log.device_mac not in stats:
            stats[log.device_mac] = {'down': 0, 'up': 0}
        stats[log.device_mac]['down'] += log.bytes_down
        stats[log.device_mac]['up'] += log.bytes_up
        
    return stats

@router.get("/speedtest/history")
def get_speedtest_history(limit: int = 10, session: Session = Depends(get_session)):
    results = session.exec(select(SpeedTestResult).order_by(SpeedTestResult.timestamp.desc()).limit(limit)).all()
    return results

@router.post("/speedtest/run")
async def trigger_speedtest():
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, run_speedtest)
    
    if result:
        return {"success": True, "data": result}
    return {"success": False, "error": "Failed to run speedtest"}

@router.get("/topology")
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
