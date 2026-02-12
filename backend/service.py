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
        # Intentar llamada directa síncrona primero (versiones antiguas)
        try:
             return mac_lookup.lookup(mac)
        except TypeError:
             pass # Es asíncrona

        # Versiones nuevas async de mac-vendor-lookup
        import asyncio
        loop = None
        try:
             loop = asyncio.get_event_loop()
        except RuntimeError:
             loop = asyncio.new_event_loop()
             asyncio.set_event_loop(loop)

        if loop.is_running():
             # Si ya hay un loop corriendo, no podemos usar run_until_complete directamente
             # Retornamos "Desconocido" temporalmente o usamos un hack
             return "Desconocido (Async)"
        
        return loop.run_until_complete(mac_lookup.lookup(mac))

    except Exception as e:
        # print(f"Error MacLookup: {e}")
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
    
    # 1. Obtener subredes adicionales de la configuración
    extra_subnets = []
    try:
        from .models import Settings
        with Session(engine) as session:
            setting = session.get(Settings, "scan_subnets")
            if setting and setting.value:
                extra_subnets = [s.strip() for s in setting.value.split(',') if s.strip()]
                print(f"📋 Subredes adicionales configuradas: {extra_subnets}")
    except Exception as e:
        print(f"⚠️ Error leyendo configuración de subredes: {e}")

    # 2. Ejecutar escaneo (auto + manual)
    active_devices = scan_network(target_cidrs=extra_subnets) 
    
    with Session(engine) as session:
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

                # 🧹 IP TAKEOVER CHECK:
                try:
                    conflicts = session.exec(select(Device).where(Device.ip == ip, Device.mac != mac, Device.status == "online")).all()
                    for old in conflicts:
                        old.status = "offline"
                        session.add(old)
                except: pass
                 
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
                
                # Check Localhost
                is_local = d.get('is_local', False)
                alias = "💻 ESTE SERVIDOR (TÚ)" if is_local else get_hostname(ip)
                is_trusted = is_local

                new_device = Device(
                    mac=mac,
                    ip=ip,
                    vendor=vendor,
                    hostname=alias, # Legacy mapping
                    alias=alias,
                    status="online",
                    last_seen=datetime.utcnow(),
                    first_seen=datetime.utcnow(),
                    is_trusted=is_trusted,
                    interface=interface
                )
                session.add(new_device)
                
                # 🧹 IP TAKEOVER CHECK (NUEVO DISPOSITIVO):
                try:
                    conflicts = session.exec(select(Device).where(Device.ip == ip, Device.mac != mac, Device.status == "online")).all()
                    for old in conflicts:
                        old.status = "offline"
                        session.add(old)
                except: pass

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


        # 3. Manejar dispositivos que ya no están (Offline)
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
