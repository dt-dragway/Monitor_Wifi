from sqlmodel import Session, select
from .models import Device, IntruderLog
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

import asyncio

def get_vendor(mac):
    try:
        # MacLookup en versiones recientes es Async o retorna coroutine
        # Usamos asyncio.run para ejecutarlo síncronamente en este contexto
        # Ojo: crear un event loop nuevo cada vez es costoso, pero funcional para este script simple
        # Si ya hay loop corriendo, esto fallara. Pero estamos en un thread aparte (background_scanner)
        # asi que deberia funcionar.
        
        try:
             # Check if we have an event loop
             loop = asyncio.get_event_loop()
        except RuntimeError:
             loop = asyncio.new_event_loop()
             asyncio.set_event_loop(loop)

        # Para versiones nuevas:
        return loop.run_until_complete(mac_lookup.lookup(mac))
    except Exception:
        # Fallback a version sincrona o error
        try:
             return mac_lookup.lookup(mac) 
        except:
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
                # Verificar si era un intruso offline que se reconectó
                was_offline = existing_device.status == "offline"
                is_intruder = not existing_device.is_trusted
                
                existing_device.ip = ip
                existing_device.last_seen = datetime.utcnow()
                existing_device.status = "online"
                existing_device.interface = d.get('interface') # Actualizar interfaz si cambia
                
                # Actualizar vendor si falta
                if not existing_device.vendor or existing_device.vendor == "Desconocido":
                     existing_device.vendor = get_vendor(mac)
                
                 # Intentar obtener hostname si no tiene alias
                if not existing_device.alias:
                     if d.get('is_local'):
                         existing_device.alias = "💻 ESTE SERVIDOR (TÚ)"
                         existing_device.is_trusted = True # Confiar en uno mismo
                     else:
                         hostname = get_hostname(ip)
                         if hostname:
                             existing_device.alias = hostname

                session.add(existing_device)
                
                # 🚨 NOTIFICAR SI UN INTRUSO SE RECONECTÓ
                if was_offline and is_intruder:
                    from .notifier import notify_intruder
                    notify_intruder({
                        'mac': mac,
                        'ip': ip,
                        'vendor': existing_device.vendor,
                        'alias': existing_device.alias
                    })
                    
                    # 📝 REGISTRAR INTRUSO EN BD
                    intruder_log = IntruderLog(
                        device_mac=mac,
                        device_ip=ip,
                        vendor=existing_device.vendor,
                        alias=existing_device.alias,
                        detection_type="reconnection"
                    )
                    session.add(intruder_log)

            else:
                # Nuevo dispositivo
                vendor = get_vendor(mac)
                interface = d.get('interface') # Obtener interfaz
                
                if d.get('is_local'):
                     alias = "💻 ESTE SERVIDOR (TÚ)"
                else:
                     hostname = get_hostname(ip)
                     alias = hostname if hostname else None
                
                is_trusted = True if d.get('is_local') else False
                
                new_device = Device(mac=mac, ip=ip, vendor=vendor, alias=alias, status="online", is_trusted=is_trusted, interface=interface)
                session.add(new_device)
                print(f"Nuevo dispositivo detectado: {ip} ({mac}) - {vendor} / {alias} [{interface}]")
                from .logger import log_event
                log_event("INFO", f"Nuevo dispositivo detectado: {vendor} ({ip})", mac)
                
                # 🚨 NOTIFICAR SI ES UN INTRUSO (no confiable)
                if not is_trusted:
                    from .notifier import notify_intruder
                    notify_intruder({
                        'mac': mac,
                        'ip': ip,
                        'vendor': vendor,
                        'alias': alias
                    })
                    
                    # 📝 REGISTRAR INTRUSO EN BD
                    intruder_log = IntruderLog(
                        device_mac=mac,
                        device_ip=ip,
                        vendor=vendor,
                        alias=alias,
                        detection_type="new_device"
                    )
                    session.add(intruder_log)


        # 2. Manejar dispositivos que ya no están (Offline)
        # Buscar dispositivos que estaban online pero NO están en active_macs
        statement = select(Device).where(Device.status == "online")
        online_devices = session.exec(statement).all()
        
        for device in online_devices:
            if device.mac not in active_macs:
                # Si no respondió, dar margen de tolerancia (Grace Period)
                # Escaneo es cada 30s. Damos 3 minutos antes de marcar offline.
                # Esto evita parpadeos si un dispositivo no responde un ARP puntual.
                GRACE_PERIOD = 180 # segundos (3 min)
                
                if device.last_seen:
                    time_diff = (datetime.utcnow() - device.last_seen).total_seconds()
                    if time_diff < GRACE_PERIOD:
                        continue # Aún consideramos online
                
                device.status = "offline"
                session.add(device)
                from .logger import log_event
                log_event("INFO", f"Dispositivo desconectado: {device.alias or device.vendor} ({device.ip})", device.mac)
        
        session.commit()
    print("Red actualizada.")
