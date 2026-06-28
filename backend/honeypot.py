import socket
import threading
from backend.logger import log_event
from datetime import datetime

class HoneyPort:
    def __init__(self, port, service_name):
        self.port = port
        self.service_name = service_name
        self.running = False
        self.socket = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.bind(('0.0.0.0', self.port))
            self.socket.listen(5)
            print(f"🍯 Honeypot activo en puerto {self.port} ({self.service_name})")
            
            while self.running:
                client, addr = self.socket.accept()
                ip = addr[0]
                message = f"🚨 ACCESO DETECTADO en Honeypot ({self.service_name}) desde IP: {ip}"
                print(message)
                log_event("DANGER", message)
                
                # ACCIÓN LETAL: Encarcelar automáticamente al atacante
                try:
                    from backend.jail import jailer
                    # Intentamos obtener la MAC si el scanner la detectó previamente
                    from backend.database import engine
                    from backend.models import Device
                    from sqlmodel import Session, select
                    
                    mac = None
                    with Session(engine) as session:
                        device = session.exec(select(Device).where(Device.ip == ip)).first()
                        if device: mac = device.mac
                    
                    # Ejecutar castigo
                    jailer.add_prisoner(ip, mac)
                    log_event("DANGER", f"🚔 CONTRAMEDIDA ACTIVADA: IP {ip} enviada a prisión (Jail)")
                except Exception as e:
                    print(f"Error activando contramedida letal: {e}")

                # Simular un servicio real para engañar al atacante/scanner (mientras el jail surte efecto)
                try:
                    if self.service_name == "SSH":
                        client.send(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.1\r\n")
                    elif self.service_name == "Telnet":
                        client.send(b"\xff\xfb\x01\xff\xfb\x03\xff\xfd\x18\xff\xfd\x1f")
                except: pass
                
                client.close()
        except Exception as e:
            if self.running:
                print(f"Error en HoneyPort {self.port}: {e}")

    def stop(self):
        self.running = False
        if self.socket:
            self.socket.close()

class HoneypotManager:
    def __init__(self):
        # Puertos jugosos para hackers/scanners
        self.honey_ports = [
            HoneyPort(22, "SSH"),
            HoneyPort(23, "Telnet"),
            HoneyPort(3389, "RDP"),
            HoneyPort(445, "SMB"),
            HoneyPort(1433, "MSSQL")
        ]

    def start_all(self):
        for hp in self.honey_ports:
            hp.start()

    def stop_all(self):
        for hp in self.honey_ports:
            hp.stop()

# Instancia global
honeypot_manager = HoneypotManager()
