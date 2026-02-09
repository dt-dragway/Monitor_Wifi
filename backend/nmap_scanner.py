import nmap
import asyncio

nm = nmap.PortScanner()

def scan_device_details(ip):
    """
    Realiza un escaneo intenso a una IP específica para detectar SO y puertos.
    Retorna un diccionario con los detalles.
    """
    print(f"Iniciando escaneo detallado para {ip}...")
    try:
        # Escaneo silencioso, detección de OS (-O), versión (-sV)
        # Requiere root para -O
        nm.scan(ip, arguments='-O -sV --version-intensity 5')
        
        if ip not in nm.all_hosts():
            return {"error": "Host no accesible o bloqueado"}

        host_data = nm[ip]
        
        # Extraer OS
        os_match = "Desconocido"
        if 'osmatch' in host_data and host_data['osmatch']:
            os_match = host_data['osmatch'][0]['name']
            
        # Extraer Puertos
        open_ports = []
        if 'tcp' in host_data:
            for port in host_data['tcp']:
                state = host_data['tcp'][port]['state']
                name = host_data['tcp'][port]['name']
                product = host_data['tcp'][port].get('product', '')
                version = host_data['tcp'][port].get('version', '')
                if state == 'open':
                    open_ports.append(f"{port}/tcp ({name}) {product} {version}".strip())

        return {
            "os": os_match,
            "ports": open_ports,
            "hostname": host_data.hostname() if host_data.hostname() else None
        }

    except Exception as e:
        print(f"Error en Nmap: {e}")
        return {"error": str(e)}

def scan_vulnerabilities(ip):
    """
    Ejecuta scripts de vulnerabilidades de Nmap contra la IP.
    """
    print(f"Iniciando auditoría de vulnerabilidades para {ip}...")
    try:
        # --script vuln: Ejecuta scripts de detección de vulnerabilidades conocidas
        # Esto puede tardar bastante.
        nm.scan(ip, arguments='-sV --script vuln')
        
        if ip not in nm.all_hosts():
            return {"error": "Host no accesible"}

        host_data = nm[ip]
        if 'hostscript' in host_data:
            # Nmap devuelve los resultados de scripts en 'hostscript'
            return {"vulnerabilities": host_data['hostscript']}
        
        # También buscar en puertos específicos
        vulns = []
        if 'tcp' in host_data:
            for port in host_data['tcp']:
                if 'script' in host_data['tcp'][port]:
                    for script_name, output in host_data['tcp'][port]['script'].items():
                        vulns.append({"script": script_name, "output": output, "port": port})
        
        return {"vulnerabilities": vulns}

    except Exception as e:
        print(f"Error audits: {e}")
        return {"error": str(e)}
