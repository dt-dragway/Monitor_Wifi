import time
import threading
import socket
import os
import scapy.all as scapy
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

# Utilidad para respuestas DNS falsas (Captive Portal)
class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = ''
        tipo = (data[2] >> 3) & 15
        if tipo == 0:
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini+1:ini+lon+1].decode() + '.'
                ini += lon + 1
                lon = data[ini]

    def response(self, ip):
        packet = b''
        if self.domain:
            packet += self.data[:2] + b"\x81\x80"
            packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'
            packet += self.data[12:]
            packet += b'\xc0\x0c'
            packet += b'\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'
            packet += bytes(map(int, ip.split('.')))
        return packet

# Configuración
WARNING_HTML_PATH = "/media/Jesus-Aroldo/Anexo/Desarrollos  /Monitor_Wifi/templates/warning.html"

def get_default_iface_name():
    try:
        route = scapy.conf.route.route("8.8.8.8")
        return route[0]
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
    REDIRECT_IP = "192.168.1.1" # Overwritten by Jailer

    def do_GET(self):
        host = self.headers.get('Host', '')
        path = self.path
        
        is_probe = any(x in path for x in [
            'generate_204', 'check_network_status', 'hotspot-detect.html', 
            'ncsi.txt', 'success.html', 'connectivity-check'
        ])

        if host.startswith(self.REDIRECT_IP) or host == "127.0.0.1":
            if path == "/" or path.startswith("/static") or is_probe:
                self._serve_warning_page()
            else:
                self._send_redirect()
            return

        self._send_redirect()

    def _send_redirect(self):
        self.send_response(302)
        self.send_header('Location', f'http://{self.REDIRECT_IP}/')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.end_headers()

    def _serve_warning_page(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Connection', 'close')
            self.end_headers()
            
            if os.path.exists(WARNING_HTML_PATH):
                with open(WARNING_HTML_PATH, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write("<h1>NetGuard: Acceso Bloqueado</h1>".encode())
        except Exception as e:
            pass

    def log_message(self, format, *args):
        pass

class Jailer:
    def __init__(self):
        self.victims = {}
        self.running = False
        self.lock = threading.Lock()
        self.iface = get_default_iface_name()
        self.local_ip = get_local_ip(self.iface)
        self.gateway_ip = self._get_gateway_ip()
        self.web_thread = None
        self.dns_thread = None
        self.arp_thread = None
        self.dnssocket = None

    def _get_gateway_ip(self):
        try:
            return scapy.conf.route.route("0.0.0.0")[2]
        except:
            return "192.168.0.1"

    def _get_gateway_mac(self):
        try:
            ans, unans = scapy.srp(scapy.Ether(dst="ff:ff:ff:ff:ff:ff")/scapy.ARP(pdst=self.gateway_ip), timeout=2, verbose=False)
            for s, r in ans:
                return r.hwsrc
        except:
            return "ff:ff:ff:ff:ff:ff"

    def _get_active_interfaces(self):
        interfaces = []
        try:
            for iface in scapy.get_if_list():
                if iface == 'lo': continue
                if scapy.get_if_addr(iface) != "0.0.0.0":
                    interfaces.append(iface)
        except: pass
        return interfaces or [self.iface]

    def start(self):
        if self.running: return
        self.running = True
        self.interfaces = self._get_active_interfaces()
        os.system("sysctl -w net.ipv4.ip_forward=1 > /dev/null")
        self.web_thread = threading.Thread(target=self._run_web_server, daemon=True)
        self.web_thread.start()
        self.dns_thread = threading.Thread(target=self._run_dns_server, daemon=True)
        self.dns_thread.start()
        self.arp_thread = threading.Thread(target=self._run_arp_loop, daemon=True)
        self.arp_thread.start()

    def stop(self):
        self.running = False
        if self.dnssocket:
            try: self.dnssocket.close()
            except: pass
        with self.lock:
             for ip in list(self.victims.keys()):
                 self.release_prisoner(ip)

    def add_prisoner(self, ip, mac=None):
        with self.lock:
            if ip not in self.victims:
                self.victims[ip] = mac
                # Reglas de IPTables (Misma agresividad)
                os.system(f"iptables -t nat -I PREROUTING -s {ip} -p tcp --dport 80 -j REDIRECT --to-ports 80")
                os.system(f"iptables -t nat -I PREROUTING -s {ip} -p udp --dport 53 -j REDIRECT --to-ports 53")
                os.system(f"iptables -I FORWARD -s {ip} -j REJECT --reject-with icmp-admin-prohibited")
                
                # BURST ARP MUY AGRESIVO (Aumentado a 20 para forzar el cambio de tabla ARP instantáneo)
                self._send_arp_burst(ip, mac, count=20)
                
                try:
                    from backend.forensics import evidence_collector
                    evidence_collector.start_capture(ip, mac)
                except: pass
                self._notify_jailed(ip, mac)

    def _notify_jailed(self, ip, mac):
        try:
            from backend.notifier import send_desktop_notification
            from backend.database import engine
            from backend.models import Device
            from sqlmodel import Session, select
            device_name = "Dispositivo"
            if mac:
                with Session(engine) as session:
                    d = session.exec(select(Device).where(Device.mac == mac)).first()
                    if d: device_name = d.alias or d.vendor or "Dispositivo"
            send_desktop_notification(title="🚔 ENCARCELADO", message=f"{device_name}\nIP: {ip}", urgency="critical")
        except: pass

    def release_prisoner(self, ip):
        with self.lock:
            if ip in self.victims:
                del self.victims[ip]
                os.system(f"iptables -t nat -D PREROUTING -s {ip} -p tcp --dport 80 -j REDIRECT --to-ports 80")
                os.system(f"iptables -t nat -D PREROUTING -s {ip} -p udp --dport 53 -j REDIRECT --to-ports 53")
                os.system(f"iptables -D FORWARD -s {ip} -j REJECT --reject-with icmp-admin-prohibited")
                self._restore_arp(ip)
                try:
                    from backend.forensics import evidence_collector
                    evidence_collector.stop_capture(ip)
                except: pass

    def _run_web_server(self):
        try:
            WarningHandler.REDIRECT_IP = self.local_ip 
            server = HTTPServer(('0.0.0.0', 80), WarningHandler)
            server.serve_forever()
        except: pass

    def _run_dns_server(self):
        try:
            self.dnssocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.dnssocket.bind(('0.0.0.0', 53))
            while self.running:
                try:
                    data, addr = self.dnssocket.recvfrom(1024)
                    p = DNSQuery(data)
                    self.dnssocket.sendto(p.response(self.local_ip), addr)
                except: pass
        except: pass

    def _send_arp_burst(self, ip, mac=None, count=10):
        gw_mac = self._get_gateway_mac()
        target_mac = mac if mac else "ff:ff:ff:ff:ff:ff"
        for iface in self.interfaces:
            try:
                # Decirle a la víctima que YO soy el router
                pkt1 = scapy.ARP(op=2, pdst=ip, hwdst=target_mac, psrc=self.gateway_ip)
                # Decirle al router que YO soy la víctima
                pkt2 = scapy.ARP(op=2, pdst=self.gateway_ip, hwdst=gw_mac, psrc=ip)
                scapy.send(pkt1, count=count, verbose=False, iface=iface)
                scapy.send(pkt2, count=count, verbose=False, iface=iface)
            except: pass

    def _run_arp_loop(self):
        gw_mac = self._get_gateway_mac()
        while self.running:
            with self.lock:
                targets = dict(self.victims)
            for ip, mac in targets.items():
                for iface in self.interfaces:
                    try:
                        target_mac = mac if mac else "ff:ff:ff:ff:ff:ff"
                        # Enviar ráfaga pequeña continua (0.5s de intervalo total)
                        scapy.send(scapy.ARP(op=2, pdst=ip, hwdst=target_mac, psrc=self.gateway_ip), verbose=False, iface=iface)
                        scapy.send(scapy.ARP(op=2, pdst=self.gateway_ip, hwdst=gw_mac, psrc=ip), verbose=False, iface=iface)
                    except: pass
            time.sleep(0.5) # Más frecuente para "martillar" la tabla ARP

    def _restore_arp(self, ip):
        try:
             real_mac = scapy.getmacbyip(self.gateway_ip)
             for iface in self.interfaces:
                 packet = scapy.ARP(op=2, pdst=ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=self.gateway_ip, hwsrc=real_mac)
                 scapy.send(packet, count=3, verbose=False, iface=iface)
        except: pass

jailer = Jailer()
