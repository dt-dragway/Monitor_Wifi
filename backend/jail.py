import time
import threading
import socket
import os
import scapy.all as scapy
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

# Configuración
WARNING_HTML_PATH = "templates/warning.html"

def get_default_iface_name():
    try:
        # Intenta obtener la interfaz por defecto (la que tiene ruta a internet)
        route = scapy.conf.route.route("8.8.8.8")
        return route[0] # Interfaz (ej: eno1, wlan0)
    except:
        return scapy.conf.iface

def get_local_ip(iface=None):
    try:
        if iface:
             return scapy.get_if_addr(iface)
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class WarningHandler(SimpleHTTPRequestHandler):
    REDIRECT_IP = "192.168.0.1" # Default fallback, overwritten by Jailer

    def do_GET(self):
        # PORTAL CAUTIVO STANDARD BEHAVIOR
        # Android: /generate_204 -> Espera 204. Si recibe otra cosa (200 o 302), lanza popup.
        # iOS: /hotspot-detect.html -> Espera "Success". Si recibe otra cosa, lanza popup.
        # Windows: /ncsi.txt -> Espera "Microsoft NCSI".
        
        # Estrategia: "Captive Portal Detection"
        # 1. Si piden nuestra IP root ("/"), mostrar la Alerta.
        # 2. Si piden CUALQUIER otra cosa, REDIRIGIR (302) a nuestra IP root.
        
        # Identificar si la request va dirigida a nuestra IP local
        host = self.headers.get('Host', '')
        
        # Si ya están en nuestra IP y path raiz, mostrar alerta
        if host.startswith(self.REDIRECT_IP) and (self.path == "/" or self.path.startswith("/static")):
            self._serve_warning_page()
            return
            
        # Para todo lo demás (Google, Apple, etc), REDIRIGIR A LA ALERTA
        # Esto confirma al OS que hay un portal cautivo.
        self.send_response(302)
        self.send_header('Location', f'http://{self.REDIRECT_IP}/')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()

    def _serve_warning_page(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            
            if os.path.exists(WARNING_HTML_PATH):
                with open(WARNING_HTML_PATH, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write("""
                    <html>
                    <body style="background-color:black; color:red; text-align:center; padding-top:50px; font-family:sans-serif;">
                        <h1 style="font-size:50px;">🚫 ACCESO BLOQUEADO 🚫</h1>
                        <h2>Tu dispositivo ha sido detectado como INTRUSO.</h2>
                        <p>Esta red está monitoreada activamente.</p>
                    </body>
                    </html>
                """.encode("utf-8"))
        except Exception as e:
            print(f"Error sirviendo web: {e}")

    def log_message(self, format, *args):
        pass # Silenciar logs

class Jailer:
    def __init__(self):
        self.victims = {} # IP -> MAC (Dict for specific targeting)
        self.running = False
        self.lock = threading.Lock()
        self.iface = get_default_iface_name()
        self.local_ip = get_local_ip(self.iface)
        self.gateway_ip = self._get_gateway_ip()
        
        # Threads
        self.web_thread = None
        self.dns_thread = None
        self.arp_thread = None
        self.dnssocket = None

    def _get_gateway_ip(self):
        try:
            return scapy.conf.route.route("0.0.0.0")[2]
        except:
            return "192.168.0.1"

    def _get_active_interfaces(self):
        """Devuelve una lista de interfaces activas con IP"""
        interfaces = []
        try:
            for iface in scapy.get_if_list():
                if iface == 'lo': continue
                # Solo interfaces con IP
                if scapy.get_if_addr(iface) != "0.0.0.0":
                    interfaces.append(iface)
        except: pass
        if not interfaces:
             # Fallback
             interfaces = [self.iface]
        return interfaces

    def start(self):
        if self.running: return
        self.running = True
        
        self.interfaces = self._get_active_interfaces()
        print(f"🚔 Wall of Shame (Jailer) Iniciado en {', '.join(self.interfaces)}")
        
        os.system("sysctl -w net.ipv4.ip_forward=1 > /dev/null")

        # 1. Web Server
        self.web_thread = threading.Thread(target=self._run_web_server, daemon=True)
        self.web_thread.start()

        # 2. DNS Server
        self.dns_thread = threading.Thread(target=self._run_dns_server, daemon=True)
        self.dns_thread.start()

        # 3. ARP Spoofer
        self.arp_thread = threading.Thread(target=self._run_arp_loop, daemon=True)
        self.arp_thread.start()

    def stop(self):
        self.running = False
        if self.dnssocket:
            try: self.dnssocket.close()
            except: pass
            
        with self.lock:
             # Release all on stop
             for ip, mac in list(self.victims.items()):
                 self.release_prisoner(ip)

    def add_prisoner(self, ip, mac=None):
        with self.lock:
            if ip not in self.victims:
                print(f"🚔 Encarcelando a {ip} ({mac or 'Unknown MAC'}) - TODAS LAS REDES")
                self.victims[ip] = mac
                
                # PORTAL CAUTIVO AGRESIVO (GLOBAL - SIN INTERFAZ ESPECIFICA):
                # Aplicamos reglas sin -i {iface} para que afecten a cualquier interfaz de entrada
                
                # 1. HTTP a nosotros (REDIRECT)
                os.system(f"iptables -t nat -I PREROUTING -s {ip} -p tcp --dport 80 -j REDIRECT --to-ports 80")
                
                # 2. DNS a nosotros (REDIRECT)
                os.system(f"iptables -t nat -I PREROUTING -s {ip} -p udp --dport 53 -j REDIRECT --to-ports 53")
                
                # 3. Bloquear HTTPS y TODO el tráfico restante (ICMP, UDP juegos, etc)
                os.system(f"iptables -I FORWARD -s {ip} -p tcp --dport 443 -j REJECT --reject-with tcp-reset")
                os.system(f"iptables -I FORWARD -s {ip} -p udp --dport 443 -j REJECT")

                self._send_arp_burst(ip, mac)
                
                # 🚨 NOTIFICACIÓN DE DISPOSITIVO ENCARCELADO
                self._notify_jailed(ip, mac)
    
    def _notify_jailed(self, ip, mac):
        """Envía notificación cuando un dispositivo es encarcelado"""
        try:
            # Importar aquí para evitar dependencias circulares
            from backend.notifier import send_desktop_notification
            from backend.database import engine
            from backend.models import Device
            from sqlmodel import Session, select
            
            # Obtener información del dispositivo desde la BD
            device_name = "Dispositivo Desconocido"
            vendor = "Desconocido"
            
            if mac:
                with Session(engine) as session:
                    statement = select(Device).where(Device.mac == mac)
                    device = session.exec(statement).first()
                    if device:
                        device_name = device.alias or device.vendor or "Dispositivo Desconocido"
                        vendor = device.vendor or "Desconocido"
            
            # Enviar notificación de escritorio
            title = "🚔 DISPOSITIVO ENCARCELADO"
            message = f"{device_name}\nIP: {ip}\nMAC: {mac or 'N/A'}\n\n⚠️ Redirigido a página cautiva"
            
            send_desktop_notification(
                title=title,
                message=message,
                urgency="critical",
                icon="security-medium"
            )
            
            print(f"✅ Notificación de Jail enviada para {ip}")
            
        except Exception as e:
            print(f"⚠️ Error enviando notificación de Jail: {e}")


    def release_prisoner(self, ip):
        with self.lock:
            if ip in self.victims:
                print(f"🏳️ Liberando a {ip}")
                del self.victims[ip]
                
                # Limpiar (Sin interface especifica)
                # Nota: El orden de borrado (-D) no importa tanto como -I
                os.system(f"iptables -t nat -D PREROUTING -s {ip} -p tcp --dport 80 -j REDIRECT --to-ports 80")
                os.system(f"iptables -t nat -D PREROUTING -s {ip} -p udp --dport 53 -j REDIRECT --to-ports 53")
                os.system(f"iptables -D FORWARD -s {ip} -p tcp --dport 443 -j REJECT --reject-with tcp-reset")
                os.system(f"iptables -D FORWARD -s {ip} -p udp --dport 443 -j REJECT")
                
                self._restore_arp(ip)

    def _send_arp_burst(self, ip, mac=None):
        # Enviar burst en TODAS las interfaces activas por si acaso
        # El switch/AP se encargará de enrutar
        try:
            target_mac = mac if mac else "ff:ff:ff:ff:ff:ff"
            print(f"DEBUG: Enviando ARP Poison a {ip} ({target_mac}) en interfaces: {self.interfaces}")
            
            for iface in self.interfaces:
                try:
                    # Gateway de esta interfase?
                    # Simplificacion: Usamos la gateway global detectada o la IP de la interfase como source
                    # Mejor: Spoofear siendo el Gateway GLOBAL detectado
                    # Si multicast, llegará.
                    
                    pkt1 = scapy.ARP(op=2, pdst=ip, hwdst=target_mac, psrc=self.gateway_ip)
                    # Tell Gateway I am victim
                    pkt2 = scapy.ARP(op=2, pdst=self.gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=ip)
                    
                    scapy.send(pkt1, count=3, verbose=False, iface=iface)
                    scapy.send(pkt2, count=3, verbose=False, iface=iface)
                except Exception as e:
                    print(f"DEBUG: Error enviando ARP en {iface}: {e}")
        except Exception as e:
            print(f"DEBUG: Error general en ARP burst: {e}")
    
    def _run_web_server(self):
        try:
            # Bind to 0.0.0.0 to accept traffic from victims
            server = HTTPServer(('0.0.0.0', 80), WarningHandler)
            
            # CRITICAL FIX: Inject real LAN IP into handler for redirects
            WarningHandler.REDIRECT_IP = self.local_ip 
            
            print(f"🕸️ Servidor Web Trampa escuchando en puerto 80 (Redirect IP: {self.local_ip})")
            server.serve_forever()
        except OSError:
             print("⚠️ Puerto 80 ocupado. No se puede iniciar servidor web trampa.")

    def _run_dns_server(self):
        print(f"🕸️ Servidor DNS Trampa ONLINE (:53)")
        try:
            self.dnssocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.dnssocket.bind(('0.0.0.0', 53))
            
            while self.running:
                try:
                    data, addr = self.dnssocket.recvfrom(1024)
                    p = DNSQuery(data)
                    self.dnssocket.sendto(p.response(self.local_ip), addr)
                except:
                    pass
        except: pass

    def _run_arp_loop(self):
        while self.running:
            with self.lock:
                targets = dict(self.victims) # Copy dict
            
            # Refresh active interfaces dynamically? Maybe heavy. Keep static for now.
            
            for ip, mac in targets.items():
                for iface in self.interfaces:
                    try:
                        target_mac = mac if mac else "ff:ff:ff:ff:ff:ff"
                        # Victim -> Attacker -> Gateway
                        scapy.send(scapy.ARP(op=2, pdst=ip, hwdst=target_mac, psrc=self.gateway_ip), verbose=False, iface=iface)
                        # Gateway -> Attacker -> Victim
                        scapy.send(scapy.ARP(op=2, pdst=self.gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=ip), verbose=False, iface=iface)
                    except:
                        pass
            time.sleep(2)

    def _restore_arp(self, ip):
        try:
             real_mac = scapy.getmacbyip(self.gateway_ip)
             for iface in self.interfaces:
                 packet = scapy.ARP(op=2, pdst=ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=self.gateway_ip, hwsrc=real_mac)
                 scapy.send(packet, count=3, verbose=False, iface=iface)
        except:
             pass

jailer = Jailer()
