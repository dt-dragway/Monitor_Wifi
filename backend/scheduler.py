import threading
import time
from sqlmodel import Session, select

from backend.database import engine
from backend.models import Device
from backend.service import update_network_status
from backend.blocker import blocker
from backend.jail import jailer
from backend.honeypot import honeypot_manager
from backend.traffic_analyzer import start_sniffer_thread
from backend.speedtest_monitor import run_speedtest

scanning_active = True

def background_scanner():
    """Hilo que ejecuta el escaneo periódicamente"""
    while scanning_active:
        try:
            update_network_status()
        except Exception as e:
            print(f"Error en escaneo: {e}")
        time.sleep(30) # Escanear cada 30 segundos

def speedtest_scheduler():
    while scanning_active:
        time.sleep(14400) # 4 horas
        try:
            run_speedtest()
        except Exception as e:
            print(f"Error scheduled speedtest: {e}")

def restore_persistence():
    print("♻️ Restaurando reglas de bloqueo desde base de datos...")
    with Session(engine) as session:
        blocked_devices = session.exec(select(Device).where(Device.is_blocked == True)).all()
        for device in blocked_devices:
            print(f"🔒 Bloqueando persistente: {device.ip} ({device.mac})")
            if device.ip:
                 jailer.add_prisoner(device.ip, device.mac)
            blocker.block_device(device.mac)

def start_all_background_tasks():
    global scanning_active
    scanning_active = True
    
    # Iniciar hilo de escaneo
    t = threading.Thread(target=background_scanner, daemon=True)
    t.start()
    
    # Iniciar módulos de seguridad
    blocker.start()
    jailer.start()
    honeypot_manager.start_all() # Iniciar Honeypot profesional
    start_sniffer_thread() # Traffic Analyzer (Phase 21)

    # Iniciar scheduler de speedtest
    t_st = threading.Thread(target=speedtest_scheduler, daemon=True)
    t_st.start()

    # Restaurar bloqueos
    restore_persistence()

def stop_all_background_tasks():
    global scanning_active
    scanning_active = False
