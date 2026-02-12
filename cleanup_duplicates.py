
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Device
from sqlalchemy import func

print("🧹 Iniciando limpieza de duplicados...")

with Session(engine) as session:
    # 1. Buscar todas las IPs duplicadas que están online
    ips = session.exec(select(Device.ip).where(Device.status=="online")).all()
    
    # Contar ocurrencias
    from collections import Counter
    counts = Counter(ips)
    
    duplicates = [ip for ip, count in counts.items() if count > 1 and ip != "0.0.0.0"]
    
    if not duplicates:
        print("✅ No se encontraron duplicados activos.")
    
    for ip in duplicates:
        print(f"🔧 Procesando IP duplicada: {ip}")
        # Obtener dispositivos con esta IP ordenados por last_seen (el más reciente al final)
        devs = session.exec(select(Device).where(Device.ip == ip, Device.status == "online").order_by(Device.last_seen)).all()
        
        # El último es el "real" (más reciente). Los anteriores son fantasmas.
        real_device = devs[-1]
        ghosts = devs[:-1]
        
        for ghost in ghosts:
            print(f"   💀 Marcando OFFLINE fantasma: {ghost.mac} ({ghost.alias})")
            ghost.status = "offline"
            session.add(ghost)
            
    session.commit()
    print("✨ Base de datos optimizada.")
