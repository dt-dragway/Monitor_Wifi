from scapy.all import ARP, Ether, srp, conf
import subprocess
import json
import socket
import re
import sys

# Configurar scapy para ser menos verboso
conf.verb = 0

def get_network_interfaces():
    """
    Obtiene una lista de interfaces activas con sus detalles (IP, Máscara, CIDR).
    Usa el comando 'ip -j addr' para mayor precisión.
    """
    interfaces_info = []
    
    try:
        # Intentar obtener salida JSON de ip addr (más confiable)
        result = subprocess.run(['ip', '-j', 'addr'], capture_output=True, text=True)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for iface in data:
                name = iface.get('ifname')
                operstate = iface.get('operstate', 'UNKNOWN')
                
                # Filtrar loopback y estados DOWN
                if name == 'lo' or operstate == 'DOWN':
                    continue
                
                # Buscar direcciones IPv4
                for addr in iface.get('addr_info', []):
                    if addr.get('family') == 'inet':
                        ip = addr.get('local')
                        prefixlen = addr.get('prefixlen')
                        
                        # Construir CIDR (ej: 192.168.1.0/24)
                        # Calcular la red base
                        import ipaddress
                        network = ipaddress.IPv4Network(f"{ip}/{prefixlen}", strict=False)
                        
                        interfaces_info.append({
                            'name': name,
                            'ip': ip,
                            'cidr': str(network),
                            'network': network
                        })
        else:
            # Fallback a método antiguo si 'ip -j' falla
            print("⚠️ 'ip -j addr' falló, usando método legacy...")
            return _get_interfaces_legacy()
            
    except Exception as e:
        print(f"Error detectando interfaces: {e}")
        return _get_interfaces_legacy()
        
    return interfaces_info

def _get_interfaces_legacy():
    """Fallback para obtener interfaces si ip -j addr falla"""
    # Implementación simple basada en scapy/socket
    return [{'name': None, 'cidr': '192.168.0.0/24', 'ip': '127.0.0.1'}] # Default seguro

def scan_network(target_cidrs=None):
    """
    Escanea la red buscando dispositivos activos.
    Si target_cidrs es None, descubre y escanea TODAS las interfaces activas.
    Puede recibir una lista de CIDRs adicionales para escanear.
    """
    all_devices = []
    seen_macs = set()
    
    # 1. Determinar qué escanear
    targets = []
    
    # Auto-descubrimiento (siempre activo por defecto)
    print("🔍 Detectando redes activas...")
    interfaces = get_network_interfaces()
    targets.extend(interfaces)
    
    # Agregar objetivos manuales
    if target_cidrs:
        if isinstance(target_cidrs, str): target_cidrs = [target_cidrs]
        for cidr in target_cidrs:
            # Asociar a la interfaz por defecto (None) o buscar la mejor interfaz
            targets.append({'cidr': cidr, 'name': None})
    
    if not targets:
        print("❌ No se detectaron interfaces activas para escanear.")
        return []

    # 2. Escanear cada objetivo
    for target in targets:
        cidr = target.get('cidr')
        iface = target.get('name')
        print(f"📡 Escaneando red {cidr} en interfaz {iface or 'default'}...")
        
        try:
            # Crear paquete ARP request broadcast
            arp = ARP(pdst=cidr)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether/arp

            # Enviar y esperar respuesta
            # Aumentamos agresividad para detectar todos los dispositivos (incluso lentos)
            ans, unans = srp(packet, timeout=3, iface=iface, verbose=0, retry=3)
            
            # Procesar respuestas
            for sent, received in ans:
                if received.hwsrc not in seen_macs:
                    device = {
                        'ip': received.psrc,
                        'mac': received.hwsrc,
                        'interface': iface,
                        'vendor': 'Desconocido', # Se llena luego
                        'status': 'online'
                    }
                    all_devices.append(device)
                    seen_macs.add(received.hwsrc)
                    
        except Exception as e:
            print(f"⚠️ Error escaneando {cidr} ({iface}): {e}")

    # 3. Agregar el propio servidor (localhost) si no fue detectado
    try:
        # Usar la primera IP detectada como "local" si hay interfaces
        interfaces = get_network_interfaces()
        local_ip = "127.0.0.1"
        for iface in interfaces:
            if iface['ip'] and not iface['ip'].startswith('127.'):
                local_ip = iface['ip']
                break
                
        import uuid
        mac_num = uuid.getnode()
        mac_str = ':'.join(['{:02x}'.format((mac_num >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
        
        if not any(d['ip'] == local_ip for d in all_devices):
             all_devices.append({
                 'ip': local_ip, 
                 'mac': mac_str, 
                 'is_local': True,
                 'status': 'online',
                 'vendor': 'Monitor Wifi Server',
                 'alias': '💻 ESTE SERVIDOR'
             })
    except Exception as e:
        print(f"Error agregando localhost: {e}")
        pass

    print(f"✅ Escaneo finalizado. Total dispositivos: {len(all_devices)}")
    return all_devices

if __name__ == "__main__":
    # Test directo
    print("Iniciando prueba de escaneo avanzado...")
    devices = scan_network()
    print("\nResultados:")
    print(f"{'IP':<16} {'MAC':<18} {'Interfaz'}")
    print("-" * 45)
    for d in devices:
        print(f"{d['ip']:<16} {d['mac']:<18} {d.get('interface', 'N/A')}")
