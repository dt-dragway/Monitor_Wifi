from sqlmodel import Session, select
from .models import Device
from .scanner import scan_network
from .database import engine
from mac_vendor_lookup import MacLookup
from datetime import datetime

# Inicializar MacLookup (puede tardar la primera vez en descargar la DB)
mac_lookup = MacLookup()
# mac_lookup.update_vendors() # Descomentar para actualizar la DB localmente si es necesario

import socket
from mac_vendor_lookup import MacLookup

# Inicializar MacLookup
mac_lookup = MacLookup()

def get_vendor(mac):
    try:
        # Forzamos la carga si es necesaria, pero en versions nuevas MacLookup puede ser async.
        # Si es la version async, deberíamos usar AsyncMacLookup.
        # Vamos a intentar usar un "truco" para bajar la base de datos sícronamente o manejarlo mejor.
        # En la version 0.1.x de mac-vendor-lookup, `lookup` lee de un archivo local.
        # El error anterior sugiere que se está usando una interfaz async.
        # Vamos a leer el archivo directamente o manejarlo con una lista estática si falla mucho.
        # O MEJOR: Usamos requests a una API externa o simplemente atrapamos el error bien.
        
        # Intento simple síncrono
        return mac_lookup.lookup(mac)
    except Exception:
        return "Desconocido"

def get_hostname(ip):
    try:
        data = socket.gethostbyaddr(ip)
        return data[0]
    except Exception:
        return None

def update_network_status():
    """
    Ejecuta un escaneo, actualiza dispositivos existentes y crea nuevos.
    Marca como offline los que no responden.
    """
    print("Iniciando actualización de red...")
    active_devices = scan_network() 
    
    with Session(engine) as session:
        # 1. Marcar todos como offline temporalmente? O mejor comparar.
        # Estrategia: Obtener todos los dispositivos de la DB.
        # Los que están en active_devices -> online + update timestamp
        # Los que NO están en active_devices -> offline (si su last_seen es antiguo)
        
        active_macs = set()

        for d in active_devices:
            mac = d['mac']
            ip = d['ip']
            active_macs.add(mac)
            
            # Buscar si ya existe
            statement = select(Device).where(Device.mac == mac)
            results = session.exec(statement)
            existing_device = results.first()
            
            if existing_device:
                existing_device.ip = ip
                existing_device.last_seen = datetime.utcnow()
                existing_device.status = "online"
                
                # Actualizar vendor si falta
                if not existing_device.vendor or existing_device.vendor == "Desconocido":
                     existing_device.vendor = get_vendor(mac)
                
                # Intentar obtener hostname si no tiene alias
                if not existing_device.alias:
                     hostname = get_hostname(ip)
                     if hostname:
                         existing_device.alias = hostname

                session.add(existing_device)
            else:
                # Nuevo dispositivo
                vendor = get_vendor(mac)
                hostname = get_hostname(ip)
                alias = hostname if hostname else None
                
                new_device = Device(mac=mac, ip=ip, vendor=vendor, alias=alias, status="online", is_trusted=False)
                session.add(new_device)
                print(f"Nuevo dispositivo detectado: {ip} ({mac}) - {vendor} / {alias}")

        # 2. Manejar dispositivos que ya no están (Offline)
        # Buscar dispositivos que estaban online pero NO están en active_macs
        statement = select(Device).where(Device.status == "online")
        online_devices = session.exec(statement).all()
        
        for device in online_devices:
            if device.mac not in active_macs:
                # Si no respondió en este escaneo, marcar como offline
                # Podría darse un margen de tolerancia (ej: 2 escaneos perdidos), pero por ahora directo.
                device.status = "offline"
                session.add(device)
        
        session.commit()
    print("Red actualizada.")
