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

def scan_network(ip_range=None):
    """
    Escanea la red utilizando peticiones ARP.
    Retorna una lista de diccionarios con IP y MAC.
    """
    if ip_range is None:
        ip_range = get_network_range()
        
    print(f"Iniciando escaneo en {ip_range}...")
    
    try:
        # Crear paquete ARP request
        arp = ARP(pdst=ip_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        # Enviar paquete y recibir respuesta
        # timeout: tiempo de espera por respuesta
        result = srp(packet, timeout=3, verbose=0)[0]

        devices = []
        for sent, received in result:
            devices.append({'ip': received.psrc, 'mac': received.hwsrc})

        # AGREGAR EL PROPIO SERVIDOR (LOCALHOST) A LA LISTA
        # Scapy no se detecta a sí mismo en ARP scan
        try:
             local_ip = get_local_ip()
             # Intentar obtener la MAC de la interfaz correcta
             # Esto es un best-effort, puede fallar en alquinos entornos docker/vms
             import uuid
             mac_num = uuid.getnode()
             mac_str = ':'.join(['{:02x}'.format((mac_num >> elements) & 0xff) for elements in range(0,2*6,2)][::-1])
             
             # Verificar si ya está en la lista (raro, pero por si acaso)
             if not any(d['ip'] == local_ip for d in devices):
                 # Es el servidor
                 devices.append({'ip': local_ip, 'mac': mac_str, 'is_local': True})
        except:
             pass

        print(f"Escaneo completado. Dispositivos encontrados: {len(devices)}")
        return devices
    except PermissionError:
        print("Error: Permiso denegado. Se requieren privilegios de root (sudo) para escaneo ARP.")
        return []
    except Exception as e:
        print(f"Error en escaneo: {e}")
        return []

if __name__ == "__main__":
    target_ip = get_network_range()
    print(f"Detectado rango de red: {target_ip}")
    found_devices = scan_network(target_ip)
    print("Dispositivos encontrados:")
    print("IP" + " "*18+"MAC")
    for device in found_devices:
        print("{:16}    {}".format(device['ip'], device['mac']))
