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
    def do_GET(self):
        # Captive Portal behavior: Redirect everything to /
        if self.path != "/" and not self.path.startswith("/static"):
             self.send_response(302)
             self.send_header('Location', f'http://{self.server.server_address[0]}/')
             self.end_headers()
             return

        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
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
        self.victims = set()
        self.running = False
        self.lock = threading.Lock()
        self.iface = get_default_iface_name()
        self.local_ip = get_local_ip(self.iface)
        self.gateway_ip = self._get_gateway_ip()
        
        # Threads
        self.web_thread = None
        self.arp_thread = None

    def _get_gateway_ip(self):
        try:
            return scapy.conf.route.route("0.0.0.0")[2]
        except:
            return "192.168.0.1"

    def start(self):
        if self.running: return
        self.running = True
        
        print(f"🚔 Wall of Shame (Jailer) Iniciado en {self.iface} ({self.local_ip})")
        
        # Enable IP Forwarding (Critical for MITM)
        os.system("sysctl -w net.ipv4.ip_forward=1 > /dev/null")

        # 1. Start Web Server
        self.web_thread = threading.Thread(target=self._run_web_server, daemon=True)
        self.web_thread.start()

        # 2. Start ARP Spoofer
        self.arp_thread = threading.Thread(target=self._run_arp_loop, daemon=True)
        self.arp_thread.start()

    def stop(self):
        self.running = False
        # Disable IP Forwarding (Security best practice to revert)
        # os.system("sysctl -w net.ipv4.ip_forward=0 > /dev/null") 
        # Better not strictly disable to avoid breaking other things, but cleaning iptables is key.
        for ip in list(self.victims):
            self.release_prisoner(ip)

    def add_prisoner(self, ip):
        with self.lock:
            if ip not in self.victims:
                print(f"🚔 Encarcelando a {ip}")
                self.victims.add(ip)
                
                # REDIRECTION RULES (The Trap)
                # 1. Redirect HTTP (80) to us (Captive Portal)
                # Usamos --to-ports porque es mas compatible que --to-destination
                os.system(f"iptables -t nat -I PREROUTING -i {self.iface} -s {ip} -p tcp --dport 80 -j REDIRECT --to-ports 80")
                
                # 2. Redirect DNS (53) to us (Packet Fence style) - Force them to resolve through us
                # This ensures we can answer ANY DNS query with our own IP if we wanted, 
                # but since we don't have a custom DNS server running in this script (only scapy which is slow),
                # A better approach is simply BLOCKING external DNS so they are forced to deal with ARP spoofing?
                # No, let's Redirect DNS to Google (8.8.8.8) BUT since we ARP spoof, we are the gateway.
                # If we want the 'Connect to Network' popup, we need to answer DNS.
                # Since implementing a full DNS server is complex, we rely on the ARP Redirect + HTTP Redirect.
                # When they try to browse http://neverssl.com, it hits our port 80.
                
                # 3. Hijack HTTPS (443) & Block Real DNS (53)
                # Redirecting 443 to 80 causes 'SSL Protocol Error'.
                # Rejecting it causes 'Connection Refused'. 
                # Rejecting is faster and forces fallback to HTTP often.
                os.system(f"iptables -I FORWARD -s {ip} -p tcp --dport 443 -j REJECT --reject-with tcp-reset")
                os.system(f"iptables -I FORWARD -s {ip} -p udp --dport 443 -j REJECT") # QUIC

                # BLOCK REAL DNS (So only our spoofed response works)
                os.system(f"iptables -I FORWARD -s {ip} -p udp --dport 53 -j DROP")
                os.system(f"iptables -I FORWARD -s {ip} -p tcp --dport 53 -j DROP")

                # 4. Trigger ARP
                self._send_arp_burst(ip)

    def release_prisoner(self, ip):
        with self.lock:
            if ip in self.victims:
                print(f"🏳️ Liberando a {ip}")
                self.victims.remove(ip)
                # Clean Rules
                os.system(f"iptables -t nat -D PREROUTING -i {self.iface} -s {ip} -p tcp --dport 80 -j REDIRECT --to-ports 80")
                os.system(f"iptables -D FORWARD -s {ip} -p tcp --dport 443 -j REJECT --reject-with tcp-reset")
                os.system(f"iptables -D FORWARD -s {ip} -p udp --dport 443 -j REJECT")
                
                # Clean DNS Block
                os.system(f"iptables -D FORWARD -s {ip} -p udp --dport 53 -j DROP")
                os.system(f"iptables -D FORWARD -s {ip} -p tcp --dport 53 -j DROP")
                
                self._restore_arp(ip)

    def _send_arp_burst(self, ip):
        print(f"⚡ ARP Burst a {ip}")
        try:
            # Tell victim I am Gateway
            pkt1 = scapy.ARP(op=2, pdst=ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=self.gateway_ip)
            # Tell Gateway I am victim
            pkt2 = scapy.ARP(op=2, pdst=self.gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=ip)
            
            scapy.send(pkt1, count=5, verbose=False, iface=self.iface)
            scapy.send(pkt2, count=5, verbose=False, iface=self.iface)
        except:
             pass

    def _run_web_server(self):
        try:
            # Bind to 0.0.0.0 to accept traffic from victims
            server = HTTPServer(('0.0.0.0', 80), WarningHandler)
            print("🕸️ Servidor Web Trampa escuchando en puerto 80")
            server.serve_forever()
        except OSError:
             print("⚠️ Puerto 80 ocupado. No se puede iniciar servidor web trampa.")

    def _run_arp_loop(self):
        while self.running:
            with self.lock:
                targets = list(self.victims)
            
            if not targets:
                time.sleep(1)
                continue

            for ip in targets:
                try:
                    # Man in the Middle (Poison both sides)
                    # Victim -> Attacker -> Gateway
                    scapy.send(scapy.ARP(op=2, pdst=ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=self.gateway_ip), verbose=False, iface=self.iface)
                    # Gateway -> Attacker -> Victim
                    scapy.send(scapy.ARP(op=2, pdst=self.gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=ip), verbose=False, iface=self.iface)
                except:
                    pass
            time.sleep(2) # Refresh rate

    def _restore_arp(self, ip):
        try:
             real_mac = scapy.getmacbyip(self.gateway_ip)
             packet = scapy.ARP(op=2, pdst=ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=self.gateway_ip, hwsrc=real_mac)
             scapy.send(packet, count=3, verbose=False, iface=self.iface)
        except:
             pass

jailer = Jailer()
