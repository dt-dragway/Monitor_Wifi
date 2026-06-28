import scapy.all as scapy
import threading
import os
import time
from datetime import datetime
from backend.logger import log_event

PCAP_DIR = "security_audits/captures"

class TrafficEvidenceCollector:
    """
    Módulo profesional de recolección de evidencia forense.
    Capaz de capturar y guardar tráfico específico de intrusos encarcelados para análisis posterior.
    """
    def __init__(self):
        self.active_sniffers = {} # ip -> stop_event
        if not os.path.exists(PCAP_DIR):
            os.makedirs(PCAP_DIR, exist_ok=True)
            
    def start_capture(self, ip, mac=None):
        """Inicia un sniffer dedicado para una IP específica"""
        if ip in self.active_sniffers:
            return
            
        print(f"🕵️ Iniciando recolección de evidencia para {ip}...")
        stop_event = threading.Event()
        self.active_sniffers[ip] = stop_event
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{PCAP_DIR}/evidence_{ip.replace('.', '_')}_{timestamp}.pcap"
        
        thread = threading.Thread(
            target=self._sniff_worker, 
            args=(ip, filename, stop_event),
            daemon=True
        )
        thread.start()
        
        log_event("WARNING", f"🕵️ Grabación forense iniciada para {ip}. Archivo: {filename}")
        return filename

    def stop_capture(self, ip):
        """Detiene la captura para una IP"""
        if ip in self.active_sniffers:
            self.active_sniffers[ip].set()
            del self.active_sniffers[ip]
            print(f"🛑 Grabación forense finalizada para {ip}")

    def _sniff_worker(self, ip, filename, stop_event):
        """Worker thread que realiza el sniffing filtrado"""
        # Filtro BPF para capturar solo tráfico de/hacia la IP de interés
        bpf_filter = f"host {ip}"
        
        pkts = []
        
        def process_packet(pkt):
            pkts.append(pkt)
            # Guardamos cada 50 paquetes para no saturar memoria o al final
            if len(pkts) >= 50:
                scapy.wrpcap(filename, pkts, append=True)
                pkts.clear()

        # Sniff loop con timeout pequeño para chequear el stop_event
        try:
            while not stop_event.is_set():
                scapy.sniff(
                    filter=bpf_filter, 
                    prn=process_packet, 
                    timeout=2, 
                    count=0, # infinitos mientras dure el timeout
                    store=0
                )
            
            # Guardar remanentes
            if pkts:
                scapy.wrpcap(filename, pkts, append=True)
        except Exception as e:
            print(f"Error en sniffer forense ({ip}): {e}")

# Instancia global
evidence_collector = TrafficEvidenceCollector()
