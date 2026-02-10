from scapy.all import ARP, Ether, srp
import socket
import sys

def get_local_ip():
    """Obtiene la IP local de la máquina"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No necesita ser alcanzable realmente
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_network_range():
    """Calcula el rango de red /24 basado en la IP local"""
    local_ip = get_local_ip()
    if local_ip == '127.0.0.1':
        return "192.168.1.0/24" # Fallback
    
    # Asumimos mascara /24 estándar para redes domésticas
    base_ip = ".".join(local_ip.split('.')[:-1]) + ".0/24"
    return base_ip

def _get_active_interfaces():
    """Devuelve una lista de interfaces activas con IP"""
    interfaces = []
    try:
        import scapy.all as scapy
        for iface in scapy.get_if_list():
            if iface == 'lo': continue
            try:
                if scapy.get_if_addr(iface) != "0.0.0.0":
                    interfaces.append(iface)
            except: pass
    except: pass
    return interfaces

def scan_network(ip_range=None):
    """
    Escanea la red utilizando peticiones ARP en TODAS las interfaces.
    """
    if ip_range is None:
        ip_range = get_network_range()
        
    print(f"Iniciando escaneo en {ip_range}...")
    
    devices = []
    seen_macs = set()
    
    # Obtener interfaces
    interfaces = _get_active_interfaces()
    # Si no hay interfaces detectadas, intentar con la default implícita de scapy (fallback)
    if not interfaces:
        interfaces = [None] 

    for iface in interfaces:
        try:
            print(f"Escaneando interfaz: {iface}...")
            # Crear paquete ARP request
            arp = ARP(pdst=ip_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether/arp

            # Enviar paquete y recibir respuesta
            # timeout: tiempo de espera por respuesta
            # iface=None usa default, sino usa la especifica
            result = srp(packet, timeout=2, verbose=0, iface=iface)[0]

            for sent, received in result:
                if received.hwsrc not in seen_macs:
                    devices.append({'ip': received.psrc, 'mac': received.hwsrc, 'interface': iface})
                    seen_macs.add(received.hwsrc)
        except PermissionError:
            print(f"Error Permisos en {iface}: Se requiere sudo.")
        except Exception as e:
            print(f"Error escaneando {iface}: {e}")

    # AGREGAR EL PROPIO SERVIDOR (LOCALHOST) A LA LISTA
    try:
         local_ip = get_local_ip()
         import uuid
         mac_num = uuid.getnode()
         mac_str = ':'.join(['{:02x}'.format((mac_num >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
         
         if not any(d['ip'] == local_ip for d in devices):
             devices.append({'ip': local_ip, 'mac': mac_str, 'is_local': True})
    except:
         pass

    print(f"Escaneo completado. Dispositivos encontrados: {len(devices)}")
    return devices

if __name__ == "__main__":
    target_ip = get_network_range()
    print(f"Detectado rango de red: {target_ip}")
    found_devices = scan_network(target_ip)
    print("Dispositivos encontrados:")
    print("IP" + " "*18+"MAC")
    for device in found_devices:
        print("{:16}    {}".format(device['ip'], device['mac']))
