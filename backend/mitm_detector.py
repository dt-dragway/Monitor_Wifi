import os
import re
import scapy.all as scapy
from concurrent.futures import ThreadPoolExecutor
import time

class MITMDetector:
    def __init__(self):
        self.gateway_ip = self._get_gateway_ip()
        self.gateway_mac = self._get_mac(self.gateway_ip) if self.gateway_ip else None
        self.status = "secure" # secure, warning, danger
        self.alerts = []
        self.last_check = 0

    def _get_gateway_ip(self):
        """Obtiene la IP del Gateway predeterminado"""
        try:
            # Comando ip route | grep default
            result = os.popen("ip route show | grep default").read()
            # Extract IP: default via 192.168.0.1 ...
            match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", result)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def _get_mac(self, ip):
        """Obtiene la MAC de una IP usando Scapy"""
        try:
            arp_request = scapy.ARP(pdst=ip)
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast/arp_request
            answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]

            if answered_list:
                return answered_list[0][1].hwsrc
        except:
            pass
        return None

    def check_security(self):
        """
        Verifica la integridad de la red.
        Retorna el estado actual de seguridad.
        """
        # Evitar chequeos demasiado frecuentes
        if time.time() - self.last_check < 5:
            return {"status": self.status, "alerts": self.alerts}
        
        self.last_check = time.time()
        self.alerts = []
        self.status = "secure"

        if not self.gateway_ip:
            self.alerts.append("No se pudo detectar el Gateway.")
            self.status = "warning"
            return {"status": self.status, "alerts": self.alerts}

        # 1. Verificar si la MAC del Gateway ha cambiado
        current_gateway_mac = self._get_mac(self.gateway_ip)
        
        if current_gateway_mac and self.gateway_mac and current_gateway_mac != self.gateway_mac:
            self.status = "danger"
            self.alerts.append(f"¡ALERTA MITM! La MAC del Gateway cambió de {self.gateway_mac} a {current_gateway_mac}.")
        
        # Si no teniamos MAC guardada, la guardamos ahora
        if current_gateway_mac and not self.gateway_mac:
            self.gateway_mac = current_gateway_mac

        # 2. Verificar duplicidad de MACs (Un atacante suele tener su MAC + la del gateway spoofeada)
        # Esto es más complejo de detectar pasivamente sin tabla completa, 
        # pero podemos verificar si nuestra tabla ARP local ve la MAC del gateway asociada a otra IP.
        
        return {"status": self.status, "alerts": self.alerts, "gateway_ip": self.gateway_ip, "gateway_mac": self.gateway_mac}

# Instancia global
mitm_detector = MITMDetector()
