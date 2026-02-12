
from scapy.all import sniff, IP, ARP
import threading
import collections
import time
from sqlmodel import Session
from .database import engine
from .models import TrafficLog
from datetime import datetime

# {mac: {'down': 0, 'up': 0}} (Bytes)
traffic_stats = collections.defaultdict(lambda: {'down': 0, 'up': 0})
stop_sniffing = False

# Limit memory usage by flushing periodically
LAST_FLUSH = time.time()
FLUSH_INTERVAL = 60 # seconds

# Track last saved state to calculate deltas for DB
last_saved_stats = collections.defaultdict(lambda: {'down': 0, 'up': 0})

# Cache de MACs conocidas para evitar consultas DB constantes
known_macs = set()

def load_known_macs():
    try:
        from .models import Device
        with Session(engine) as session:
            devs = session.exec(select(Device.mac)).all()
            known_macs.update(devs)
        print(f"🧠 MACs conocidas cargadas: {len(known_macs)}")
    except Exception:
        pass

# Cargar al importar (o llamar explícitamente al iniciar el thread)
load_known_macs()

def register_passive_device(mac, ip=None):
    try:
        from .models import Device
        from .service import get_vendor
        
        with Session(engine) as session:
             # Doble check por concurrencia
             if session.get(Device, mac):
                 return

             vendor = get_vendor(mac)
             new_dev = Device(
                 mac=mac, 
                 ip=ip or "0.0.0.0", 
                 vendor=vendor, 
                 alias="Detectado por Sniffer", 
                 status="online", 
                 is_trusted=False,
                 interface="passive",
                 last_seen=datetime.utcnow(),
                 first_seen=datetime.utcnow()
             )
             session.add(new_dev)
             
             # 🧹 IP TAKEOVER CHECK (TIEMPO REAL):
             if ip and ip != "0.0.0.0":
                 try:
                    stmt = select(Device).where(Device.ip == ip, Device.mac != mac, Device.status == "online")
                    conflicts = session.exec(stmt).all()
                    for old in conflicts:
                        print(f"♻️ [Sniffer] Limpiando IP duplicada {ip}: vieja MAC {old.mac} -> Offline")
                        old.status = "offline"
                        session.add(old)
                 except: pass

             session.commit()
             print(f"👻 Dispositivo detectado PASIVAMENTE: {mac} ({vendor})")
    except Exception as e:
        print(f"Error registro pasivo: {e}")

def packet_callback(packet):
    global LAST_FLUSH
    try:
        pkt_len = len(packet)
        
        # Monitor IP traffic
        if IP in packet:
            # We rely on Ethernet layer if present for MAC
            if hasattr(packet, 'src'): 
                mac_src = packet.src
                traffic_stats[mac_src]['up'] += pkt_len
                
                # DETECCIÓN PASIVA (IP)
                if mac_src not in known_macs:
                    known_macs.add(mac_src)
                    try:
                        ip_src = packet[IP].src
                        threading.Thread(target=register_passive_device, args=(mac_src, ip_src), daemon=True).start()
                    except: pass
                
            if hasattr(packet, 'dst'):
                mac_dst = packet.dst
                traffic_stats[mac_dst]['down'] += pkt_len

        # Monitor ARP traffic (Device Announcement - Muy Rápido)
        elif ARP in packet:
            try:
                # ARP no siempre tiene 'src' attribute en packet level, usamos la capa ARP
                mac_src = packet[ARP].hwsrc
                if mac_src and mac_src not in known_macs:
                    known_macs.add(mac_src)
                    ip_src = packet[ARP].psrc
                    print(f"⚡ ARP detectado: {mac_src} ({ip_src})")
                    threading.Thread(target=register_passive_device, args=(mac_src, ip_src), daemon=True).start()
            except: pass
                
                # También podríamos detectar por destino, pero es menos fiable para IP (puede ser broadcast)

        # Check flush
        if time.time() - LAST_FLUSH > FLUSH_INTERVAL:
            persist_traffic_stats()
            LAST_FLUSH = time.time()
            
    except Exception:
        pass

def persist_traffic_stats():
    """
    Saves DELTA stats (since last save) to DB.
    Maintains cumulative counts in memory for live view.
    """
    try:
        count = 0
        with Session(engine) as session:
            # Iterate over current cumulative stats
            # Use list(keys) to avoid runtime error if dict changes size
            for mac, current in list(traffic_stats.items()):
                saved = last_saved_stats[mac]
                
                # Calculate Delta
                delta_down = current['down'] - saved['down']
                delta_up = current['up'] - saved['up']
                
                if delta_down <= 0 and delta_up <= 0:
                    continue
                
                # Update last saved checkpoint
                saved['down'] = current['down']
                saved['up'] = current['up']
                
                # Write DELTA to DB
                log = TrafficLog(
                    timestamp=datetime.utcnow(),
                    device_mac=mac,
                    bytes_down=delta_down,
                    bytes_up=delta_up
                )
                session.add(log)
                count += 1
            
            session.commit()
            if count > 0: print(f"💾 Tráfico (Delta) guardado: {count} dispositivos.")
            
    except Exception as e:
        print(f"Error saving traffic logs: {e}")

def start_sniffer_thread(interface=None):
    t = threading.Thread(target=_sniff_loop, args=(interface,), daemon=True)
    t.start()

def _sniff_loop(interface):
    global stop_sniffing
    print(f"🦈 Sniffer de Tráfico (Bytes) iniciado...")
    try:
        # sniff(prn=packet_callback, store=0, iface=interface)
        # Auto-detect interface if None
        sniff(prn=packet_callback, store=0) 
    except Exception as e:
        print(f"❌ Error Critical en Sniffer: {e}")

def get_traffic_stats():
    """
    Returns current session stats (deltas since last flush + current bucket).
    Actually, frontend likely wants 'Total Downloaded' or 'Current Speed'.
    For history, we use the API. For live view, let's return a special structure.
    """
    # Return dict compatible with frontend expectation
    # Previous implementation was just count.
    # New: { mac: { down: X, up: Y } }
    # Frontend needs to handle this object change.
    return {k: dict(v) for k, v in traffic_stats.items()}
