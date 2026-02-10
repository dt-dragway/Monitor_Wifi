
from scapy.all import sniff, IP, ARP
import threading
import collections
import time

# Almacena conteo de paquetes por MAC
# {mac: count}
traffic_stats = collections.defaultdict(int)
stop_sniffing = False

def packet_callback(packet):
    try:
        # Contamos paquetes Ethernet
        if hasattr(packet, 'src'):
            traffic_stats[packet.src] += 1
        if hasattr(packet, 'dst'):
            traffic_stats[packet.dst] += 1
            
    except Exception:
        pass

def start_sniffer_thread(interface=None):
    """
    Inicia el sniffer en un hilo aparte.
    """
    t = threading.Thread(target=_sniff_loop, args=(interface,), daemon=True)
    t.start()

def _sniff_loop(interface):
    global stop_sniffing
    print(f"🦈 Sniffer iniciado en segundo plano...")
    
    try:
        # store=0 vital para no llenar RAM
        # filter="ip or arp" para capturar tráfico útil
        sniff(prn=packet_callback, store=0, filter="ip or arp") 
    except Exception as e:
        print(f"❌ Error Critical en Sniffer: {e}")

def get_traffic_stats():
    """
    Retorna y resetea las estadísticas (o mantiene acumulado?).
    Para velocidad (paquetes/seg), el frontend puede calcular delta.
    Aquí devolvemos acumulado.
    """
    # Convertir a dict normal
    return dict(traffic_stats)
