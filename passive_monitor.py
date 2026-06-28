
from scapy.all import sniff, ARP, IP
from sqlmodel import Session, select
from backend.database import engine
from backend.models import Device
from backend.service import get_vendor
import threading

print("👁️ Monitor Pasivo de Intrusos Activado")
print("Escuchando tráfico ARP para detectar dispositivos nuevos al instante...")

known_macs = set()

def load_known():
    try:
        with Session(engine) as session:
            devs = session.exec(select(Device.mac)).all()
            for mac in devs: known_macs.add(mac)
        print(f"✅ Base de datos cargada: {len(known_macs)} dispositivos conocidos.")
    except Exception as e:
        print(f"Error carga DB: {e}")

load_known()

def register(mac, ip):
    try:
        vendor = get_vendor(mac)
        with Session(engine) as session:
            if not session.get(Device, mac):
                new_dev = Device(
                    mac=mac, 
                    ip=ip, 
                    vendor=vendor, 
                    alias="Detectado por Monitor Pasivo", 
                    status="online", 
                    is_trusted=False,
                    interface="passive"
                )
                session.add(new_dev)
                session.commit()
                print(f"👻 ¡NUEVO DISPOSITIVO REGISTRADO!: {mac} ({vendor}) - {ip}")
            else:
                print(f"ℹ️ Dispositivo ya existe: {mac}")
    except Exception as e:
        print(f"Error registro: {e}")

def callback(pkt):
    if ARP in pkt:
        # ARP Op 1 (Request) o 2 (Reply)
        mac = pkt[ARP].hwsrc
        ip = pkt[ARP].psrc
        
        if mac and mac not in known_macs:
            print(f"🚨 DETECCIÓN INMEDIATA (ARP): {mac} ({ip})")
            known_macs.add(mac)
            # Registrar en hilo aparte
            threading.Thread(target=register, args=(mac, ip)).start()

    elif IP in pkt and hasattr(pkt, 'src'):
        mac = pkt.src
        if mac not in known_macs:
             ip = pkt[IP].src
             print(f"🚨 DETECCIÓN INMEDIATA (IP): {mac} ({ip})")
             known_macs.add(mac)
             threading.Thread(target=register, args=(mac, ip)).start()

# Iniciar sniffing
try:
    sniff(prn=callback, store=0)
except KeyboardInterrupt:
    print("Monitor detenido.")
except Exception as e:
    print(f"Error sniffer: {e} (¿Falta sudo?)")
