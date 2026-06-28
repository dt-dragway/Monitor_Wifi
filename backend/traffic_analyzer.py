from scapy.all import sniff, IP, ARP
import threading
import collections
import time
from datetime import datetime
from sqlmodel import Session, select
from .database import engine
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import TCP, UDP
from .models import TrafficLog

# {mac: {'down': 0, 'up': 0}} (Bytes)
traffic_stats = collections.defaultdict(lambda: {'down': 0, 'up': 0})
# {mac: {app_name: total_bytes}}
app_stats = collections.defaultdict(lambda: collections.defaultdict(int))

stop_sniffing = False

# Métricas de tiempo real (Mbps)
global_throughput = 0.0  # bits per second
total_bytes_transmitted = 0
last_total_bytes = 0
last_throughput_time = time.time()
throughput_lock = threading.Lock()

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

def classify_packet(packet, pkt_len, mac_source, mac_dest):
    """Detecta la aplicación basándose en el contenido del paquete (DNS, Puertos, SNI)"""
    app = "Web/General"
    
    # 1. DNS Inspection (La más fiable)
    if packet.haslayer(DNS) and packet.getlayer(DNS).qr == 0: # Consulta DNS
        try:
            qname = packet.getlayer(DNSQR).qname.decode().lower()
            if "netflix" in qname or "nflx" in qname: app = "Netflix"
            elif "whatsapp" in qname or "whatsapp.net" in qname: app = "WhatsApp"
            elif "facebook" in qname or "fbcdn" in qname: app = "Facebook/Instagram"
            elif "google" in qname or "youtube" in qname or "googlevideo" in qname: app = "Google/YouTube"
            elif "spotify" in qname: app = "Spotify"
            elif "steam" in qname: app = "Steam/Gaming"
            elif "tiktok" in qname: app = "TikTok"
            elif "torrent" in qname or "tracker" in qname: app = "BitTorrent"
            
            if app != "Web/General":
                # Guardamos la asociación IP -> App temporalmente para el tráfico siguiente
                # (Simple cache para este prototipo)
                pass 
        except: pass

    # 2. Port-based Detection
    if packet.haslayer(TCP) or packet.haslayer(UDP):
        sport = packet.sport
        dport = packet.dport
        
        # BitTorrent (Puertos comunes y DHT)
        if 6881 <= sport <= 6889 or 6881 <= dport <= 6889 or sport == 1900 or dport == 1900:
            app = "BitTorrent"
        # Gaming / Steam
        elif dport in [27015, 27016, 27036] or sport in [27015, 27016, 27036]:
            app = "Steam/Gaming"
        # DNS
        elif dport == 53 or sport == 53:
            app = "DNS"
        # Streaming (Deteccion base por flujo pesado - heuristica simple)
        elif pkt_len > 1000 and (dport == 443 or sport == 443):
            # No podemos ver el SNI sin deep dissection pero mantenemos "Streaming/Web"
            pass

    # Sumar a las estadísticas de la App para ese dispositivo
    if mac_source in traffic_stats:
        app_stats[mac_source][app] += pkt_len
    if mac_dest in traffic_stats:
        app_stats[mac_dest][app] += pkt_len

def packet_callback(packet):
    global LAST_FLUSH
    try:
        pkt_len = len(packet)
        mac_src = None
        mac_dst = None
        
        # Monitor IP traffic
        if IP in packet:
            # Obtener MACs reales de la capa Ethernet si están disponibles
            from scapy.layers.l2 import Ether
            if Ether in packet:
                mac_src = packet[Ether].src.lower()
                mac_dst = packet[Ether].dst.lower()
            else:
                # Fallback genérico, pero preferimos Ether para MACs reales
                # Normalizar MAC a minúsculas para consistencia
                mac_src = getattr(packet, 'src', None)
                mac_dst = getattr(packet, 'dst', None)
                mac_src = mac_src.lower() if mac_src else None
                mac_dst = mac_dst.lower() if mac_dst else None

            if mac_src:
                traffic_stats[mac_src]['up'] += pkt_len
                if mac_src not in known_macs:
                    known_macs.add(mac_src)
                    try:
                        ip_src = packet[IP].src
                        threading.Thread(target=register_passive_device, args=(mac_src, ip_src), daemon=True).start()
                    except: pass
            
            if mac_dst:
                traffic_stats[mac_dst]['down'] += pkt_len

            with throughput_lock:
                global total_bytes_transmitted
                total_bytes_transmitted += pkt_len

            # CLASIFICACIÓN DE APP
            classify_packet(packet, pkt_len, mac_src, mac_dst)

        # Monitor ARP traffic (Device Announcement)
        elif ARP in packet:
            try:
                mac_src = packet[ARP].hwsrc.lower() if packet[ARP].hwsrc else None
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
                    device_mac=mac.lower(),
                    bytes_down=delta_down,
                    bytes_up=delta_up
                )
                session.add(log)
                count += 1
            
            if count > 0:
                session.commit()
                print(f"💾 Tráfico (Delta) guardado: {count} dispositivos.")
            
    except Exception as e:
        print(f"Error saving traffic logs (DB might be busy): {e}")

def _throughput_worker():
    """Calcula el rendimiento global cada segundo"""
    global global_throughput, last_total_bytes, last_throughput_time
    while not stop_sniffing:
        try:
            time.sleep(1)
            now = time.time()
            elapsed = now - last_throughput_time
            
            with throughput_lock:
                current_total = total_bytes_transmitted
                delta_bytes = current_total - last_total_bytes
                last_total_bytes = current_total
                last_throughput_time = now
            
            # bits per second = (bytes * 8) / seconds
            if elapsed > 0:
                global_throughput = (delta_bytes * 8) / elapsed
        except Exception:
            pass

def start_sniffer_thread(interface=None):
    # Iniciar calculador de throughput
    tw = threading.Thread(target=_throughput_worker, daemon=True)
    tw.start()
    
    t = threading.Thread(target=_sniff_loop, args=(interface,), daemon=True)
    t.start()

def _sniff_loop(interface):
    global stop_sniffing
    print(f"🦈 Sniffer de Tráfico (Bytes) iniciado...")
    try:
        # Si interface es None, Scapy sniffeará en todas las interfaces por defecto.
        # Es mejor ser explícito si el usuario seleccionó una.
        sniff(prn=packet_callback, store=0, iface=interface, promisc=True) 
    except Exception as e:
        print(f"❌ Error Critical en Sniffer: {e}")

def get_traffic_stats():
    """
    Returns current session stats including bypass and app classification.
    """
    return {
        "devices": {k: dict(v) for k, v in traffic_stats.items()},
        "apps": {k: dict(v) for k, v in app_stats.items()},
        "global_throughput_bps": global_throughput,
        "total_transmitted_bytes": total_bytes_transmitted
    }
